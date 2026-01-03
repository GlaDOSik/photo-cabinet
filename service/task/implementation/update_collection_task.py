from pathlib import Path
from datetime import datetime
from typing import Optional, Set, List
from uuid import uuid4, UUID
import hashlib

from domain.metadata.metadata_sets import CREATE_DATE_SET
from domain.task.pc_task import PhotoCabinetTask
from domain.task.task_type import TaskType
from domain.task.task_log_severity import TaskLogSeverity
from indexing.domain.group_type import GroupType
from vial.config import app_config
import pc_configuration
from dbe.folder import Folder, find_root as find_root_folder
from dbe.photo import Photo, find_by_path as find_photo_by_path, find_by_hash as find_photo_by_hash, get_all as get_all_photos
from indexing import metadata_indexing_service


class RunScanAndIndexingTask(PhotoCabinetTask):
    # Supported image file extensions
    IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.raw', '.cr2', '.nef', '.arw'}

    def get_type(self) -> TaskType:
        return TaskType.UPDATE_COLLECTION

    def _serialize_fields(self):
        return {"db_task_id": self.db_task_id}

    @classmethod
    def _deserialize_fields(cls, fields: dict):
        task = cls()
        task.db_task_id = fields["db_task_id"]
        return task

    def execute(self):
        self.current_folder: List[UUID] = []
        root = Path(app_config.get_configuration(pc_configuration.COLLECTION_PATH))
        
        if not root.exists():
            raise FileNotFoundError(f"Collection path does not exist: {root}")
        
        self.log_message(f"Starting collection update from: {root}")
        
        # Get or create root folder
        root_folder = self._get_or_create_folder(None, None)
        
        # First pass: count all photos for progress tracking
        photo_count = self._count_photos(root)
        self.log_message(f"Found {photo_count} photos to process")
        self.update_max_progress(photo_count)
        
        # Second pass: scan and process
        self._scan_folder(root, root_folder)
        
        # Cleanup: remove photos from database that no longer exist on disk
        # self._cleanup_missing_photos(root)
        
        self.log_message("Collection update completed")

    def _count_photos(self, folder_path: Path) -> int:
        """Recursively count all photo files in the folder."""
        count = 0
        for item in folder_path.iterdir():
            if item.is_file() and self._is_image_file(item):
                count += 1
            elif item.is_dir() and not item.is_symlink():
                count += self._count_photos(item)
        return count

    def _scan_folder(self, folder_path: Path, parent_folder: Folder):
        """Recursively scan a folder and process photos."""
        self.log_message(f"Scanning folder: {folder_path}")
        
        # Process all files in current folder
        for item in folder_path.iterdir():
            if item.is_file() and self._is_image_file(item):
                self._process_photo(item, parent_folder)
            elif item.is_dir() and not item.is_symlink():
                # Create or get folder in database
                child_folder = self._get_or_create_folder(item.name, parent_folder.id)
                self.current_folder.append(child_folder.id)
                # Recursively scan subfolder
                self._scan_folder(item, child_folder)

    def _process_photo(self, photo_path: Path, folder: Folder):
        """Process a single photo: check if exists in DB, update metadata."""
        self.log_message(f"Processing photo: {photo_path}")
        
        # Calculate relative path from collection root
        root = Path(app_config.get_configuration(pc_configuration.COLLECTION_PATH))
        relative_path = photo_path.relative_to(root)

        file_hash = self._calculate_file_hash(str(photo_path))
        existing_photo = find_photo_by_path(self.task_transaction, str(relative_path))

        if existing_photo is None:
            existing_photo = find_photo_by_hash(self.task_transaction, file_hash)

        if existing_photo is not None:
            # Could be found by hash and renamed
            if photo_path.name != existing_photo.name:
                existing_photo.name = photo_path.name
            # Could be found by hash and moved elsewhere
            if str(relative_path) != existing_photo.file_path:
                existing_photo.file_path = str(relative_path)
            # Could be found by path and change tags thus hash
            if file_hash != existing_photo.file_hash:
                existing_photo.file_hash = file_hash
            # Photo was found in limbo (was deleted at some point) - we need to bring it back
            if existing_photo.folder.is_limbo():
                existing_photo.folder_id = folder.id

            self.task_transaction.flush()
            self._save_metadata(existing_photo) # refresh file metadata
            self.increment_current_progress()
            return

        # Create new photo entity
        photo = Photo()
        photo.folder_id = folder.id
        photo.file_path = str(relative_path)
        photo.file_hash = file_hash
        photo.name = photo_path.name
        self.task_transaction.add(photo)
        self.task_transaction.flush()

        self._save_metadata(photo)
        self.increment_current_progress()

    def _save_metadata(self, photo: Photo):
        """Extract and save EXIF metadata for a photo."""
        try:
            metadata_indexing_service.create_update_metadata_index(self.task_transaction, photo)
            self.task_transaction.flush()
            search_tag_result = metadata_indexing_service.search_tag_value(self.task_transaction, photo, GroupType.CREATED_DATE_GROUP, CREATE_DATE_SET)
            create_date_result = metadata_indexing_service.get_created_date(search_tag_result)
            if create_date_result.metadata_id is not None:
                photo.metadata_index.photo_created = create_date_result.created_date
                photo.metadata_index.photo_created_origin = create_date_result.metadata_id.get_key()
            
        except Exception as e:
            self.log_message(f"Error extracting metadata for {photo.name}: {str(e)}", severity=TaskLogSeverity.WARNING)

    # TODO - archive to limbo
    def _cleanup_missing_photos(self, root_path: Path):
        """Remove photos from database that no longer exist on disk."""
        self.log_message("Cleaning up missing photos...")

        # TODO - not that way - dont get all photos
        # Get all photos from database
        all_photos = get_all_photos(self.task_transaction)
        
        deleted_count = 0
        for photo in all_photos:
            photo_full_path = root_path / photo.file_path
            if not photo_full_path.exists():
                self.log_message(f"Deleting missing photo from DB: {photo.file_path}")
                self.task_transaction.delete(photo)
                deleted_count += 1
        
        if deleted_count > 0:
            self.task_transaction.flush()
            self.log_message(f"Deleted {deleted_count} missing photos from database")

    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[UUID]) -> Folder:
        """Get existing folder or create new one."""
        # Find existing folder by querying the correct column type
        if parent_id is None:
            # Root folder
            folder = find_root_folder(self.task_transaction)
        else:
            # Non-root folder
            folder = self.task_transaction.query(Folder).filter_by(
                name=folder_name,
                parent_id=parent_id
            ).first()
        
        if folder is None:
            # Create new folder
            folder = Folder()
            folder.name = folder_name
            folder.parent_id = parent_id
            self.task_transaction.add(folder)
            self.task_transaction.flush()
        
        return folder

    def _is_image_file(self, path: Path) -> bool:
        """Check if a file is an image based on its extension."""
        return path.suffix.lower() in self.IMAGE_EXTENSIONS


    def _calculate_file_hash(self, file_path, algo="sha256", block_size=1 << 20):  # 1 MiB chunks
        h = hashlib.new(algo)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(block_size), b""):
                h.update(chunk)
        return h.hexdigest()
