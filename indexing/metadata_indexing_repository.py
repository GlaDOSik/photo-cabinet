import re
from typing import Dict
import copy

from glom import glom, PathAccessError, assign

from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_id import MetadataId, PathArray, PathStruct

VIEW_G0_ORDERING = [MetadataGroup0.FILE, MetadataGroup0.EXIF]


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
            g0_data_new["-"] = copy.deepcopy(g0_tags)
        g1_data = g0_data.get("g1")
        if g1_data is not None:
            for g1_name, g1_tags in g1_data.items():
                g0_data_new[g1_name] = copy.deepcopy(g1_tags)
        view[g0_name] = g0_data_new

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

def search_index_value(index_data: Dict, metadata_id: MetadataId):
    """
    Exact search in index.
    If g1 is not filled, searches only g0.
    If path is not filled, it searches only the root tag.
    """
    glom_path = metadata_id.get_glom_path()
    # Convert Array[0] syntax to Array.0 for glom compatibility
    converted_path = _convert_array_syntax_to_glom(glom_path)
    return glom(index_data, converted_path)


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
        if isinstance(part, PathStruct):
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


def _convert_array_syntax_to_glom(path: str) -> str:
    """Convert Array[0] syntax to Array.0 for glom compatibility."""
    # Pattern to match KeyName[index] and replace with KeyName.index
    # Matches any characters (non-greedy) before [number]
    list_index_pattern = re.compile(r'([^.\[]+)\[(\d+)\]')
    return list_index_pattern.sub(r'\1.\2', path)
