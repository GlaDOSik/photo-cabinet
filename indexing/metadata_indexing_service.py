import json
from datetime import datetime
from typing import Dict, Any, List

from glom import glom, PathAccessError, T

from dbe.photo import Photo
from domain.metadata.metadata_id import MetadataId
from indexing.domain.created_date_result import CreatedDateResult
from indexing.domain.filter_type import FilterType
from indexing.dbe.metadata_indexing_group import MetadataIndexingGroup
from exiftool.exif_service import run_command
from exiftool.exiftool_command import ExiftoolCommand, EXIFTOOL_JSON_OPT, EXIFTOOL_GROUP_OPT, EXIFTOOL_STRUCT_OPT
from indexing.domain.photo_size_result import PhotoSizeResult
from indexing.domain.searched_tags_result import SearchedTagsResult
from domain.metadata import metadata_parsers, metadata_defined

def get_photo_size(result: SearchedTagsResult) -> PhotoSizeResult:
    width = None
    width_origin = None
    height = None
    height_origin = None
    for requested_tag in result.requested_tags:
        searched_value = result.get_value(requested_tag)
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
        searched_value = result.get_value(requested_tag)
        if searched_value.value is None:
            continue
        found_metadata_id = searched_value.searched_tag
        if found_metadata_id is None:
            continue
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
            time_dt_value = result.get_value(metadata_defined.IPTC_TIME_CREATED)
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
                metadata_set.append(MetadataId(indexing_tag.g0, indexing_tag.g1, indexing_tag.tag_name, path=indexing_tag.tag_path))

    return search_tag_value_by_tags(photo, metadata_set)

## Not exact search of index
## If g1 is not defined, it first searches in tags, then in all g1 groups
def search_tag_value_by_tags(photo: Photo, requested_tags: [MetadataId]) -> SearchedTagsResult:
    result = SearchedTagsResult()
    if photo.metadata_index is None:
        return result
    
    for requested_tag in requested_tags:
        try:
            # First try: search in tags (if g1 is None) or exact g1 path
            value = search_index_value(photo.metadata_index.exif_json, requested_tag)
            result.add_result(requested_tag, requested_tag, value)
        except PathAccessError:
            # If g1 is not defined and tags search failed, try searching in all g1 keys
            if requested_tag.group_1 is None:
                g1_results = _search_in_all_g1(photo.metadata_index.exif_json, requested_tag)
                for g1_result in g1_results:
                    result.add_result(requested_tag, g1_result[0], g1_result[1])
    return result

def _search_in_all_g1(index_data: Dict, metadata_id: MetadataId) -> List:
    """
    Search for tag value across all g1 keys when g1 is not specified.
    Returns the first found value, or None if not found in any g1.
    """
    results = []
    try:
        # Get all g1 keys for the given g0 (e.g., ['IFD0', 'ExifIFD'] for 'EXIF')
        g1_keys = glom(index_data, (f'{metadata_id.group_0}.g1', T.keys()), default=[])
        
        # Try each g1 key until we find a value
        for g1_key in g1_keys:
            try:
                # Create a new MetadataId with this g1 key and search
                g1_metadata_id = MetadataId(
                    metadata_id.group_0,
                    g1_key,
                    metadata_id.tag_name,
                    path=metadata_id.path
                )
                result_value = search_index_value(index_data, g1_metadata_id)
                results.append([g1_metadata_id, result_value])
            except PathAccessError:
                # Continue to next g1 key
                continue
    except PathAccessError:
        # No g1 structure exists for this g0
        pass
    
    return results

def get_metadata_index_from_file(photo_path: str, filtering_groups: List[MetadataIndexingGroup]) -> Dict[str, Any]:
    # Create ExiftoolCommand with base options
    command = (ExiftoolCommand()
               .with_option(EXIFTOOL_JSON_OPT)
               .with_option(EXIFTOOL_GROUP_OPT)
               .with_option(EXIFTOOL_STRUCT_OPT)
               .with_file(photo_path))
    
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
                result[g0]["g1"][g1] = value
            else:
                # No g1: add to tags
                if "tags" not in result[g0]:
                    result[g0]["tags"] = {}
                result[g0]["tags"].update(value)
    
    return result


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

## Exact search in index
## If g1 is not filled, searches only g0
## If path is not filled, it searches only the root tag
def search_index_value(index_data: Dict, metadata_id: MetadataId):
    g1_part = "tags" if metadata_id.group_1 is None else f"g1.{metadata_id.group_1}"
    path_part = "" if metadata_id.path is None else f"{metadata_id.path}."
    glom_req = f"{metadata_id.group_0}.{g1_part}.{path_part}{metadata_id.tag_name}"
    return glom(index_data, glom_req)
