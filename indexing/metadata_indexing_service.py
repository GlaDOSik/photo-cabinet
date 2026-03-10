import json
from datetime import datetime
from typing import Dict, Any, List

from glom import glom, PathAccessError, T, Match, assign
from glom.matching import Optional
from vial import putils

import copy

from dbe.photo import Photo
from domain.metadata.metadata_id import MetadataId, TAG_ID_DELIMITER
from indexing.domain.created_date_result import CreatedDateResult
from indexing.domain.filter_type import FilterType
from indexing.dbe.metadata_indexing_group import MetadataIndexingGroup
from exiftool.exif_service import run_command
from exiftool.exiftool_command import ExiftoolCommand, EXIFTOOL_JSON_OPT, EXIFTOOL_GROUP_OPT, EXIFTOOL_STRUCT_OPT
from indexing.domain.photo_size_result import PhotoSizeResult
from indexing.domain.searched_tags_result import SearchedTagsResult
from domain.metadata import metadata_parsers, metadata_defined
from indexing.metadata_indexing_repository import search_index_value

def get_photo_size(result: SearchedTagsResult) -> PhotoSizeResult:
    width = None
    width_origin = None
    height = None
    height_origin = None
    for requested_tag in result.requested_tags:
        searched_value = result.get_first_value(requested_tag)
        if searched_value.value is None:
            continue
        found_metadata_id = searched_value.searched_tag
        if found_metadata_id is None:
            continue
        if "width" in found_metadata_id.tag_name.lower():
            if width is None:
                width = metadata_parsers.parse_int(searched_value.value)
                width_origin = found_metadata_id.get_key()
        if "height" in found_metadata_id.tag_name.lower():
            if height is None:
                height = metadata_parsers.parse_int(searched_value.value)
                height_origin = found_metadata_id.get_key()
    return PhotoSizeResult(width, height, width_origin, height_origin)

# returns one parsed created date from result
def get_created_date(result: SearchedTagsResult) -> CreatedDateResult:
    for requested_tag in result.requested_tags:
        searched_value = result.get_first_value(requested_tag)
        if searched_value.value is None:
            continue
        found_metadata_id = searched_value.searched_tag
        parsed_date: datetime = metadata_parsers.parse_date(searched_value.value, metadata_parsers.DATE_PATTERNS)
        if parsed_date is None:
            # Either wrong format or no date time (it could be TZ or time)
            continue
        # try to enhance with timezone metadata
        if parsed_date.tzinfo is None and found_metadata_id == metadata_defined.EXIF_DATE_TIME_ORIGINAL:
            tz_info = result.get_value_as_timezone(metadata_defined.EXIF_OFFSET_TIME_ORIG)
            if tz_info is not None:
                return CreatedDateResult(parsed_date.replace(tzinfo=tz_info), found_metadata_id)
        # try to enhance with timezone metadata
        if parsed_date.tzinfo is None and found_metadata_id == metadata_defined.EXIF_CREATE_DATE:
            tz_info = result.get_value_as_timezone(metadata_defined.EXIF_OFFSET_TIME_DIGIT)
            if tz_info is not None:
                return CreatedDateResult(parsed_date.replace(tzinfo=tz_info), found_metadata_id)
        # only date - need to enhance with time
        if found_metadata_id == metadata_defined.IPTC_DATE_CREATED:
            time_dt_value = result.get_first_value(metadata_defined.IPTC_TIME_CREATED)
            # Only IPTC date with no time - then try other metadata
            if time_dt_value.value is None:
                continue
            parsed_time = metadata_parsers.parse_time(time_dt_value.value)
            if parsed_time is None:
                continue
            return CreatedDateResult(datetime.combine(parsed_date.date(), parsed_time), found_metadata_id) # merge date and time
        return CreatedDateResult(parsed_date, found_metadata_id)
    return CreatedDateResult(None, None)


# Search tag value in index. Find in tags defined by user in DB or by default list
def search_tag_value(photo: Photo, matching_groups: List[MetadataIndexingGroup], default_tags: [MetadataId]) -> SearchedTagsResult:
    if photo.metadata_index is None:
        return SearchedTagsResult()

    metadata_set: [MetadataId] = list()
    if len(matching_groups) == 0:
        metadata_set = default_tags
    else:
        close_match_group = _get_closest_match(matching_groups)
        for indexing_tag in close_match_group.tags:
            if indexing_tag.g0 is None or indexing_tag.tag_name is None:
                pass # TODO validation problem
            else:
                path = putils.coalesce(indexing_tag.tag_path, None)
                metadata_set.append(MetadataId(indexing_tag.g0, indexing_tag.g1, indexing_tag.tag_name, path=path))

    return search_tag_value_by_tags(photo, metadata_set)

## Loose search in effective index
## If g1 is not defined, it first searches in tags, then in all g1 groups
def search_tag_value_by_tags(photo: Photo, requested_tags: [MetadataId]) -> SearchedTagsResult:
    result = SearchedTagsResult()
    if photo.metadata_index is None:
        return result
    
    for requested_tag in requested_tags:
        try:
            # First try: search in tags (if g1 is None) or exact g1 path
            search_index_value(result, photo.metadata_index.effective_json, requested_tag, False, True)
        except Exception as ex:
            pass
    return result

def get_metadata_index_from_file(photo_path: str, filtering_groups: List[MetadataIndexingGroup]) -> Dict[str, Any]:
    # Create ExiftoolCommand with base options
    command = ExiftoolCommand.read_all(photo_path)
    
    # Process each group and its filters
    for group in filtering_groups:
        for filter_item in group.filters:
            if group.filter_type == FilterType.ALLOW:
                command.include_tag(filter_item.g0, filter_item.g1, filter_item.tag_name)
            elif group.filter_type == FilterType.DENY:
                command.exclude_tag(filter_item.g0, filter_item.g1, filter_item.tag_name)
    
    # Run the command to get JSON data
    json_data: str = run_command(command)
    # Parse index
    return _parse_metadata_index(json_data)

def _parse_metadata_index(json_data: str) -> Dict[str, Any]:
    """
    Parse metadata index JSON and transform it into v4 structured format.
    
    Transforms keys like "EXIF:IFD0" into a nested structure:
    {
      "EXIF": {
        "g1": {
          "IFD0": { ... tags ... }
        }
      }
    }
    Keys without colons go into "tags" under the g0 key.
    """
    data = json.loads(json_data)
    result: Dict[str, Any] = {}
    
    # Handle both single object and array of objects
    if not isinstance(data, list):
        data = [data]
    
    for obj in data:
        for key, value in obj.items():
            # Skip SourceFile as it's not part of the transformed structure
            if key == "SourceFile":
                continue
            
            # Skip non-dict values (shouldn't happen in metadata, but be safe)
            if not isinstance(value, dict):
                continue
            
            # Split key by colon to get g0 and optionally g1
            parts = key.split(":", 1)
            g0 = parts[0]
            g1 = parts[1] if len(parts) > 1 else None
            
            # Initialize g0 entry if it doesn't exist
            if g0 not in result:
                result[g0] = {}
            
            if g1 is not None:
                # Has g1: add to g1 structure
                if "g1" not in result[g0]:
                    result[g0]["g1"] = {}
                result[g0]["g1"][g1] = _parse_values(value)
            else:
                # No g1: add to tags
                if "tags" not in result[g0]:
                    result[g0]["tags"] = {}
                result[g0]["tags"].update(_parse_values(value))
    return result

def _parse_values(values: Dict | List) -> Dict | List:
    """Parses tag structure - gets tag id and walks tag structure recursively"""
    if isinstance(values, list):
        result = []
        for value_in_list in values:
            if isinstance(value_in_list, dict) or isinstance(value_in_list, list):
                result.append(_parse_values(value_in_list))
            else:
                result.append(value_in_list)
        return result
    elif isinstance(values, dict):
        result = {}
        for tag_name, tag_data in values.items():
            tag_id = ""
            if isinstance(tag_data, dict) and "id" in tag_data and "val" in tag_data:
                tag_id = tag_data.get("id")
                tag_value = tag_data.get("val")
                if isinstance(tag_value, dict) or isinstance(tag_value, list):
                    parsed_value = _parse_values(tag_value)
                else:
                    parsed_value = tag_value
            elif isinstance(tag_data, dict) or isinstance(tag_data, list):
                parsed_value = _parse_values(tag_data)
            else:
                parsed_value = tag_data

            result[f"{tag_name}{TAG_ID_DELIMITER}{tag_id}"] = parsed_value
        return result
    return None


# Get one out of multiple groups based on which file path match is more close. We assume input groups are already
# matched by path - for example None, folder1/, folder1/folder2/
def _get_closest_match(matched_groups: [MetadataIndexingGroup]) -> MetadataIndexingGroup:
    if len(matched_groups) == 1:
        return matched_groups[0]

    # Find the group with the longest file_path_match
    # None means the most loose match (lowest priority)
    selected_group = None
    max_length = -1

    for group in matched_groups:
        if group.file_path_match is None:
            # None is the most loose match, so skip it unless all are None
            continue

        match_length = len(group.file_path_match)
        if match_length > max_length:
            max_length = match_length
            selected_group = group

    # If all groups had None file_path_match, return the first one
    if selected_group is None:
        return matched_groups[0]

    return selected_group

def validate_index(exif_or_effective_index: Dict):
    """
    Validate index structure (v4 format): root dict, each g0 group has optional
    'tags' (dict) and/or 'g1' (dict of str -> dict), at least one required.
    Raises MatchError, TypeMatchError, or ValueError on invalid structure.
    """
    g0_spec = Match({Optional("tags"): dict, Optional("g1"): Match({str: dict})})
    root_spec = Match({str: g0_spec})
    glom(exif_or_effective_index, root_spec)
    for g0_val in exif_or_effective_index.values():
        if "tags" not in g0_val and "g1" not in g0_val:
            raise ValueError("g0 group must have 'tags' or 'g1'")

def apply_user_changes(photo: Photo) -> Dict:
    copy_exif_json = copy.deepcopy(photo.metadata_index.exif_json)
    # TODO apply changes
    return copy_exif_json

def index_to_ui_view(index_data: Dict, ordering: [MetadataId]) -> Dict:
    """
    Transforms index (db format) to view
    :param index_data:
    :return:
    """
    view = {}
    for g0_name, g0_data in index_data.items():
        g0_data_new = {}
        g0_tags = g0_data.get("tags")
        if g0_tags is not None:
            g0_data_new["-"] = _deep_copy_tags(g0_tags)
        g1_data = g0_data.get("g1")
        if g1_data is not None:
            for g1_name, g1_tags in g1_data.items():
                g0_data_new[g1_name] = _deep_copy_tags(g1_tags)
        view[g0_name] = g0_data_new

    ## TODO support __order in tags (now only ordering of g0 and g1)
    # Create __order field
    for order_metadata_id in ordering:
        if order_metadata_id.group_0 is None:
            continue
        elif order_metadata_id.group_1 is None and order_metadata_id.group_0 in view:
            g0_order = view.get("__order")
            if g0_order is None:
                g0_order = []
                view["__order"] = g0_order
            g0_order.append(order_metadata_id.group_0)
        elif order_metadata_id.group_0 in view and order_metadata_id.group_1 in view.get(order_metadata_id.group_0):
            g1_order = view.get(order_metadata_id.group_0).get("__order")
            if g1_order is None:
                g1_order = []
                view.get(order_metadata_id.group_0)["__order"] = g1_order
            g1_order.append(order_metadata_id.group_1)
    return view

def _deep_copy_tags(tags: Dict | List):
    if isinstance(tags, list):
        result = []
        for value_in_list in tags:
            if isinstance(value_in_list, dict) or isinstance(value_in_list, list):
                result.append(_deep_copy_tags(value_in_list))
            else:
                result.append(value_in_list)
        return result
    elif isinstance(tags, dict):
        result = {}
        for tag_name, tag_data in tags.items():
            if isinstance(tag_data, dict) or isinstance(tag_data, list):
                tag_data_cp = _deep_copy_tags(tag_data)
            else:
                tag_data_cp = tag_data

            tag_name_split = tag_name.split(TAG_ID_DELIMITER)

            if len(tag_name_split) > 1 and tag_name_split[0] != tag_name_split[1] and len(tag_name_split[1]) > 0:
                new_tag_name = f"{tag_name_split[0]} / {tag_name_split[1]}"
            else:
                new_tag_name = tag_name_split[0]
            result[new_tag_name] = tag_data_cp
        return result