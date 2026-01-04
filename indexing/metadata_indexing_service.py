import json
from datetime import datetime
from typing import Dict, Any, List

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
    for found_metadata_id in result.searched_tags:
        if "width" in found_metadata_id.tag_name.lower():
            width_raw = result.get_value(found_metadata_id)
            if width is None:
                width = metadata_parsers.parse_int(width_raw)
                width_origin = found_metadata_id.get_key()
        if "height" in found_metadata_id.tag_name.lower():
            height_raw = result.get_value(found_metadata_id)
            if height is None:
                height = metadata_parsers.parse_int(height_raw)
                height_origin = found_metadata_id.get_key()
    return PhotoSizeResult(width, height, width_origin, height_origin)

# returns one parsed created date from result
def get_created_date(result: SearchedTagsResult) -> CreatedDateResult:
    for found_metadata_id in result.searched_tags:
        created_date_value = result.get_value(found_metadata_id)
        if created_date_value is None:
            # Probably found multiple values - not valid created date search
            continue
        parsed_date: datetime = metadata_parsers.parse_date(created_date_value, metadata_parsers.DATE_PATTERNS)
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
            time_dt_str = result.get_value(metadata_defined.IPTC_TIME_CREATED)
            # Only IPTC date with no time - then try other metadata
            if time_dt_str is None:
                continue
            parsed_time = metadata_parsers.parse_time(time_dt_str)
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

def _search_tag_recursive_all(data: Any, tag_name: str, results: List[Any]):
    """
    Recursively search for a tag name in nested dict or array structures.
    Collects all matching values into the results list.
    
    If the tag_name is found as a direct key in a dict, adds that value.
    Also recursively searches through all nested dicts and arrays.
    """
    if data is None:
        return
    
    # If it's a dict, check if tag_name is a direct key first
    if isinstance(data, dict):
        # Direct key match - add to results
        if tag_name in data:
            results.append(data[tag_name])
        
        # Also recurse into all values to find nested matches
        for value in data.values():
            _search_tag_recursive_all(value, tag_name, results)
    
    # If it's a list/array, recurse into each item
    elif isinstance(data, list):
        for item in data:
            _search_tag_recursive_all(item, tag_name, results)

def _find_path_structures_recursive(data: Any, path_name: str, results: List[Any]):
    """
    Recursively find all structures with the given path name.
    Used for single-level paths (e.g., "Look").
    Collects all matching path structures into results list.
    """
    if data is None:
        return
    
    if isinstance(data, dict):
        # Check if path exists as a direct key
        if path_name in data:
            path_data = data[path_name]
            results.append(path_data)
        
        # Recurse into all values to find nested path structures
        for value in data.values():
            _find_path_structures_recursive(value, path_name, results)
    
    elif isinstance(data, list):
        # For arrays, recurse into each item
        for item in data:
            _find_path_structures_recursive(item, path_name, results)

def _navigate_path(data: Any, path_parts: List[str], results: List[Any]):
    """
    Navigate through nested structures following the path parts exactly.
    Supports nested paths (e.g., "Look.Parameters").
    First recursively finds structures matching the first part, then navigates through remaining parts.
    Collects all matching structures at the end of the path into results.
    """
    if data is None or len(path_parts) == 0:
        return
    
    if len(path_parts) == 1:
        # Single path part - use recursive search to find all matching structures
        _find_path_structures_recursive(data, path_parts[0], results)
        return
    
    # Multiple path parts - first find all structures matching the first part
    first_part = path_parts[0]
    remaining_parts = path_parts[1:]
    first_level_structures: List[Any] = []
    _find_path_structures_recursive(data, first_part, first_level_structures)
    
    # Then navigate through remaining parts for each found structure
    for structure in first_level_structures:
        if structure is None:
            continue
        
        if isinstance(structure, list):
            # For arrays, navigate into each item
            for item in structure:
                _navigate_path(item, remaining_parts, results)
        else:
            _navigate_path(structure, remaining_parts, results)

def _search_in_structure(data: Any, tag_name: str, path: str | None) -> List[Any]:
    """
    Search for tag_name in data structure, optionally within a specific path.
    
    Path can be a single level (e.g., "Look") or nested (e.g., "Look.Parameters").
    If path is provided, navigate to that structure first, then search for tag_name within it.
    Returns a list of all matching values (can be empty, single, or multiple).
    """
    results: List[Any] = []
    
    # If path is specified, navigate to the path structure first, then search within it
    if path is not None:
        # Split path by dots to support nested paths (e.g., "Look.Parameters")
        path_parts = path.split('.')
        path_structures: List[Any] = []
        _navigate_path(data, path_parts, path_structures)
        
        # Search for tag_name within each found path structure
        for path_structure in path_structures:
            _search_tag_recursive_all(path_structure, tag_name, results)
    else:
        # No path specified - search directly in the structure
        _search_tag_recursive_all(data, tag_name, results)
    
    return results

def search_tag_value_by_tags(photo: Photo, searched_tags: [MetadataId]) -> SearchedTagsResult:
    result = SearchedTagsResult()
    if photo.metadata_index is None:
        return result
    
    for metadata_id in searched_tags:
        g0 = photo.metadata_index.exif_json.get(metadata_id.group_0)
        if g0 is None:
            continue
        
        found_values: List[Any] = []
        
        # If g1 is defined, search only in that specific g1 section
        if metadata_id.group_1 is not None:
            g1 = g0.get("g1")
            if g1 is not None:
                g1_tags = g1.get(metadata_id.group_1)
                if g1_tags is not None:
                    found_values = _search_in_structure(g1_tags, metadata_id.tag_name, metadata_id.path)
        else:
            # No g1 defined - search in tags first, then in all g1 sections
            tags = g0.get("tags")
            if tags is not None:
                found_values = _search_in_structure(tags, metadata_id.tag_name, metadata_id.path)
            
            # If not found in tags, search in all g1 sections
            if len(found_values) == 0:
                g1 = g0.get("g1")
                if g1 is not None:
                    for g1_tags in g1.values():
                        found_values = _search_in_structure(g1_tags, metadata_id.tag_name, metadata_id.path)
                        if len(found_values) > 0:
                            break
        
        # If we found values, add them to the result
        if len(found_values) > 0:
            result.searched_tags.append(metadata_id)
            result.searched_values[metadata_id.get_key()] = found_values
    
    return result

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