from typing import Dict, List

import jsonpath

from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_id import MetadataId
from indexing.domain.searched_tags_result import SearchedTagsResult

VIEW_G0_ORDERING = [MetadataGroup0.FILE, MetadataGroup0.EXIF]


def search_index_value(search_result: SearchedTagsResult|None, index_data: Dict, metadata_id: MetadataId, strict_g1: bool, strict_path: bool) -> SearchedTagsResult:
    if search_result is None:
        search_result = SearchedTagsResult()

    json_paths = metadata_id.get_json_paths(strict_g1, strict_path)
    search_items = [item for path in json_paths for item in jsonpath.query(path, index_data).items()]

    for search_item in search_items:
        searched_path = search_item[0]
        searched_value = search_item[1]
        search_result.add_result(metadata_id, MetadataId.from_json_path(searched_path), searched_value)

    return search_result


def set_index_value(index_data: Dict, metadata_id: MetadataId, value):
    search_result = search_index_value(None, index_data, metadata_id, strict_g1=True, strict_path=True)
    found = search_result.get_first_value(metadata_id)

    if found.searched_tag is not None:
        pointer = found.searched_tag.get_json_pointer()
        jsonpath.JSONPatch().replace(pointer, value).apply(index_data)
    else:
        pointer = metadata_id.get_json_pointer()
        jsonpath.JSONPatch().add(pointer, value).apply(index_data)

