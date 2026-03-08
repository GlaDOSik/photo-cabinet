from typing import Dict, List
import copy

import jsonpath

from glom import glom, PathAccessError, assign

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
    """
    Set value in index, creating structure as needed.
    Supports Array[0] syntax for lists and regular keys for dicts.
    """
    # Ensure path up to g1 exists (creates dict structure)
    try:
        glom(index_data, metadata_id.get_glom_path_g1())
    except PathAccessError as ex:
        assign(index_data, metadata_id.get_glom_path_g1(), dict(), missing=dict)
    
    base_path = metadata_id.get_glom_path_g1()
    
    # If no path is defined, tag is at root level - simple assignment
    if not metadata_id.path:
        final_path = f"{base_path}.{metadata_id.tag_name}"
        try:
            assign(index_data, final_path, value)
        except PathAccessError:
            assign(index_data, base_path, {}, missing=dict)
            assign(index_data, final_path, value)
        return

    # Build structure incrementally from path list (PathStruct = dict key, PathArray = list + index)
    current_path = f"{base_path}.{metadata_id.tag_name}"
    path_list = metadata_id.path

    for i, part in enumerate(path_list):
        is_last = i == len(path_list) - 1
        if isinstance(part, "PathStruct"):
            key_path = f"{current_path}.{part.struct_name}"
            try:
                glom(index_data, key_path)
            except PathAccessError:
                try:
                    glom(index_data, current_path)
                except PathAccessError:
                    assign(index_data, current_path, {}, missing=dict)
                if not is_last:
                    assign(index_data, key_path, {}, missing=dict)
            current_path = key_path
        else:
            # PathArray: ensure list exists, then extend to index
            list_path = f"{current_path}.{part.array_name}"
            try:
                existing = glom(index_data, list_path)
                if not isinstance(existing, list):
                    assign(index_data, list_path, [])
            except PathAccessError:
                try:
                    glom(index_data, current_path)
                except PathAccessError:
                    assign(index_data, current_path, {}, missing=dict)
                assign(index_data, list_path, [])
            current_path = list_path

            comp_value = part.array_index
            try:
                current_list = glom(index_data, current_path)
                if not isinstance(current_list, list):
                    raise ValueError(f"Expected list at {current_path}, but got {type(current_list).__name__}")
                if len(current_list) <= comp_value:
                    needed = comp_value - len(current_list) + 1
                    if not is_last:
                        current_list.extend([{} for _ in range(needed)])
                    else:
                        current_list.extend([None] * needed)
                    assign(index_data, current_path, current_list)
            except PathAccessError:
                needed = comp_value + 1
                if not is_last:
                    current_list = [{} for _ in range(needed)]
                else:
                    current_list = [None] * needed
                assign(index_data, current_path, current_list)
            current_path = f"{current_path}.{comp_value}"

    assign(index_data, current_path, value)

