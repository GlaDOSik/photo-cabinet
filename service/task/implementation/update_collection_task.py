from pathlib import Path
from datetime import datetime
from typing import Optional, Set, List
from uuid import uuid4, UUID
import hashlib

from domain.app_data_field import AppDataField
from domain.metadata.metadata_sets import CREATE_DATE_SET
from domain.task.pc_task import PhotoCabinetTask
from domain.task.task_type import TaskType
from domain.task.task_log_severity import TaskLogSeverity
from domain.folder_type import FolderType
from indexing.domain.photo_size_result import PhotoSizeResult
from vial.config import app_config
import pc_configuration
from dbe.folder import Folder, find_root as find_root_folder, find_limbo, get_all_by_type, ROOT_FOLDER_ID
from dbe.photo import Photo, find_by_path as find_photo_by_path, find_by_hash as find_photo_by_hash, get_all_paginated
from indexing import metadata_indexing_facade
from dbe.app_data import get_app_data_val
from service import image_facade


class RunScanAndIndexingTask(PhotoCabinetTask):
    # Supported image file extensions
    IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.raw', '.cr2', '.nef', '.arw'}

    def __init__(self):
        self.existing_folders: Set[UUID] = set()
        self.existing_photos: Set[UUID] = set()
        self.thumbnail_generation_enabled = False
        self.thumbnail_size = 10
        self.thumbnail_quality = 85

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
        self.thumbnail_generation_enabled = get_app_data_val(self.task_transaction, AppDataField.THUMBNAIL_GENERATION)
        self.thumbnail_size = get_app_data_val(self.task_transaction, AppDataField.THUMBNAIL_SIZE_PX)
        self.thumbnail_quality = get_app_data_val(self.task_transaction, AppDataField.THUMBNAIL_QUALITY)

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
        self._cleanup_missing_data(root)
        
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

        file_hash = image_facade.compute_pixel_sha256(str(photo_path))
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
            self.existing_photos.add(existing_photo.id)
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
        self.existing_photos.add(photo.id)
        self.increment_current_progress()

    def _save_metadata(self, photo: Photo):
        """Extract and save EXIF metadata for a photo."""
        try:
            metadata_indexing_facade.create_update_metadata_index(self.task_transaction, photo)
            self.task_transaction.flush()

            created_date_tags = metadata_indexing_facade.search_created_date_tags(self.task_transaction, photo)
            create_date_result = metadata_indexing_facade.get_created_date(created_date_tags)
            if create_date_result.metadata_id is not None:
                photo.metadata_index.photo_created = create_date_result.created_date
                photo.metadata_index.photo_created_origin = create_date_result.metadata_id.get_key()

            if self.thumbnail_generation_enabled:
                image_facade.generate_thumbnail(photo, self.thumbnail_size, self.thumbnail_quality)

            photo_size_tags = metadata_indexing_facade.search_photo_size_tags(self.task_transaction, photo)
            photo_size_result: PhotoSizeResult = metadata_indexing_facade.get_photo_size(photo, photo_size_tags)
            photo.metadata_index.width = photo_size_result.width
            photo.metadata_index.height = photo_size_result.height
            photo.metadata_index.size_origin = f"Width: {photo_size_result.width_origin}, Height: {photo_size_result.height_origin}"

            photo.metadata_index.preview_color_hex = image_facade.get_dominant_color_quantize(photo)
            
        except Exception as e:
            self.log_message(f"Error extracting metadata for {photo.name}: {str(e)}", severity=TaskLogSeverity.WARNING)

    def _cleanup_missing_data(self, root_path: Path):
        """Move photos and folders that no longer exist on disk to limbo."""
        self.log_message("Starting cleanup of missing photos and folders")
        
        # Get limbo folder
        limbo_folder = find_limbo(self.task_transaction)
        if limbo_folder is None:
            self.log_message("Limbo folder not found, skipping cleanup", severity=TaskLogSeverity.WARNING)
            return
        
        # Cleanup photos: move to limbo if not in existing_photos
        batch_size = 1000
        offset = 0
        photos_moved = 0
        
        while True:
            photos = get_all_paginated(self.task_transaction, offset=offset, limit=batch_size)
            if not photos:
                break
            
            for photo in photos:
                if photo.id not in self.existing_photos:
                    photo.folder_id = limbo_folder.id
                    photos_moved += 1
            
            self.task_transaction.flush()
            offset += batch_size
        
        if photos_moved > 0:
            self.log_message(f"Moved {photos_moved} photos to limbo")
        
        # Cleanup folders: delete COLLECTION folders not in existing_folders
        offset = 0
        folders_deleted = 0
        
        while True:
            folders = get_all_by_type(self.task_transaction, FolderType.COLLECTION, offset=offset, limit=batch_size)
            if not folders:
                break
            
            for folder in folders:
                if folder.id not in self.existing_folders:
                    # Skip root and limbo folders
                    if folder.id != ROOT_FOLDER_ID and folder.id != limbo_folder.id:
                        self.task_transaction.delete(folder)
                        folders_deleted += 1
            
            self.task_transaction.flush()
            offset += batch_size
        
        if folders_deleted > 0:
            self.log_message(f"Deleted {folders_deleted} folders that no longer exist")

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
            folder.folder_type = FolderType.COLLECTION
            self.task_transaction.add(folder)
            self.task_transaction.flush()

        self.existing_folders.add(folder.id)
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
