from datetime import datetime
from uuid import UUID

from domain.task.pc_task import PhotoCabinetTask
from domain.task.task_type import TaskType
from dbe.photo import Photo
from indexing.dbe.metadata_index import MetadataIndex
from indexing.dbe.metadata_cache import MetadataCache, find_by_metadata_index_id
from indexing import metadata_indexing_service


class CacheMetadataTask(PhotoCabinetTask):
    """
    Fetches full metadata for a photo and stores it in MetadataCache.
    Assumes MetadataCache row already exists with task_id set — caller is responsible for creating it.
    """

    def __init__(self, metadata_index_id: UUID = None):
        super().__init__()
        self.metadata_index_id = metadata_index_id

    def get_type(self) -> TaskType:
        return TaskType.CACHE_METADATA

    def _serialize_fields(self) -> dict:
        return {
            "db_task_id": self.db_task_id,
            "metadata_index_id": str(self.metadata_index_id),
        }

    @classmethod
    def _deserialize_fields(cls, fields: dict):
        task = cls(metadata_index_id=UUID(fields["metadata_index_id"]))
        task.db_task_id = fields["db_task_id"]
        return task

    def execute(self):
        metadata_index: MetadataIndex = self.task_transaction.get(MetadataIndex, self.metadata_index_id)
        if metadata_index is None:
            raise ValueError(f"MetadataIndex not found: {self.metadata_index_id}")

        photo: Photo = self.task_transaction.get(Photo, metadata_index.photo_id)
        if photo is None:
            raise ValueError(f"Photo not found for MetadataIndex: {self.metadata_index_id}")

        full_json = metadata_indexing_service.get_metadata_index_from_file(photo.get_photo_file_path(), [])

        cache: MetadataCache = find_by_metadata_index_id(self.task_transaction, self.metadata_index_id)
        if cache is None:
            raise ValueError(f"MetadataCache not found for MetadataIndex: {self.metadata_index_id} — caller must create it before submitting the task")
        cache.full_json = full_json
        cache.created_at = datetime.utcnow()
        cache.task_id = None
