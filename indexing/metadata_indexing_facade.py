from typing import List

from sqlalchemy.orm import Session

from dbe.photo import Photo
from domain.metadata.metadata_sets import CREATE_DATE_SET, PHOTO_SIZE_SET
from indexing.dbe.metadata_index import MetadataIndex
from indexing.dbe.metadata_indexing_group import find_matching_groups, MetadataIndexingGroup
from indexing.domain.created_date_result import CreatedDateResult
from indexing.domain.group_type import GroupType
from indexing import metadata_indexing_service
from indexing.domain.photo_size_result import PhotoSizeResult
from indexing.domain.searched_tags_result import SearchedTagsResult
from service import image_service


def create_update_metadata_index(session: Session, photo: Photo):
    # Get all matching groups (global and path-specific)
    filtering_groups: List[MetadataIndexingGroup] = find_matching_groups(session, photo.file_path, GroupType.INDEXING_FILTER)
    parsed_metadata = metadata_indexing_service.get_metadata_index_from_file(photo.get_photo_file_path(), filtering_groups)

    if photo.metadata_index is None:
        metadata_index = MetadataIndex()
        metadata_index.photo_id = photo.id
        session.add(metadata_index)
        photo.metadata_index = metadata_index

    photo.metadata_index.exif_json = parsed_metadata

def search_created_date_tags(session: Session, photo: Photo) -> SearchedTagsResult:
    groups: List[MetadataIndexingGroup] = find_matching_groups(session, photo.file_path, GroupType.CREATED_DATE_GROUP)
    return metadata_indexing_service.search_tag_value(photo, groups, CREATE_DATE_SET)

def get_created_date(result: SearchedTagsResult) -> CreatedDateResult:
    return metadata_indexing_service.get_created_date(result)

def search_photo_size_tags(session: Session, photo: Photo) -> SearchedTagsResult:
    groups: List[MetadataIndexingGroup] = find_matching_groups(session, photo.file_path, GroupType.PHOTO_SIZE_GROUP)
    return metadata_indexing_service.search_tag_value(photo, groups, PHOTO_SIZE_SET)

def get_photo_size(photo: Photo, result: SearchedTagsResult) -> PhotoSizeResult:
    result: PhotoSizeResult = metadata_indexing_service.get_photo_size(result)
    if result.width is None or result.height is None:
        width, height = image_service.get_image_size(photo.get_photo_file_path())
        result.width = width
        result.height = height
        result.width_origin = "Image"
        result.height_origin = result.width_origin
    return result

