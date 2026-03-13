from datetime import datetime
from uuid import UUID

from dbe.app_data import get_app_data_val
from dbe.photo import Photo, find_by_id as find_photo_by_id
from domain.app_data_field import AppDataField
from domain.task.pc_task import PhotoCabinetTask
from domain.task.task_type import TaskType
from indexing import metadata_indexing_service
from indexing.dbe.metadata_cache import MetadataLiveCache, find_by_photo_id, delete_expired


class CacheMetadataTask(PhotoCabinetTask):
    """
    Fetches full metadata for a photo and stores it in MetadataLiveCache.
    Cleans up expired caches before writing.
    """

    def __init__(self, photo_id: UUID = None):
        super().__init__()
        self.photo_id = photo_id

    def get_type(self) -> TaskType:
        return TaskType.CACHE_METADATA

    def get_photo_id(self):
        return self.photo_id

    def _serialize_fields(self) -> dict:
        return {
            "db_task_id": self.db_task_id,
            "photo_id": str(self.photo_id),
        }

    @classmethod
    def _deserialize_fields(cls, fields: dict):
        task = cls(photo_id=UUID(fields["photo_id"]))
        task.db_task_id = fields["db_task_id"]
        return task

    def execute(self):
        photo: Photo = find_photo_by_id(self.task_transaction, self.photo_id)
        if photo is None:
            raise ValueError(f"Photo not found: {self.photo_id}")

        full_json = metadata_indexing_service.get_metadata_index_from_file(photo.get_photo_file_path(), [])

        ttl_sec = get_app_data_val(self.task_transaction, AppDataField.FILE_METADATA_CACHE_VALIDITY_SEC)
        delete_expired(self.task_transaction, int(ttl_sec))

        cache = find_by_photo_id(self.task_transaction, self.photo_id)
        if cache is None:
            cache = MetadataLiveCache(photo_id=self.photo_id)
            self.task_transaction.add(cache)

        cache.full_json = full_json
        cache.created_at = datetime.utcnow()
