import datetime
from typing import Dict, Any, List, Optional

from domain.metadata import metadata_parsers
from domain.metadata.metadata_id import MetadataId


class SearchedValue:
    def __init__(self, searched_tag: MetadataId, value):
        self.searched_tag: MetadataId = searched_tag
        self.value = value

class SearchedTagsResult:
    def __init__(self):
        self.requested_tags: List[MetadataId] = list()
        self.values_by_requested_tag: Dict[str, List[SearchedValue]] = dict()
        self.values_by_searched_tag: Dict[str, List[SearchedValue]] = dict()

    def add_result(self, requested_tag: MetadataId, searched_tag: MetadataId, value):
        if isinstance(value, list):
            for result_value in value:
                self._add_result(requested_tag, searched_tag, result_value)
        else:
            self._add_result(requested_tag, searched_tag, value)

    def _add_result(self, requested_tag: MetadataId, searched_tag: MetadataId, value):
        self.requested_tags.append(requested_tag)
        searched_value = SearchedValue(searched_tag, value)

        values_by_req = self.values_by_requested_tag.get(requested_tag.get_key())
        if values_by_req is None:
            values_by_req = []
            self.values_by_requested_tag[requested_tag.get_key()] = values_by_req
        values_by_req.append(searched_value)

        values_by_se = self.values_by_searched_tag.get(searched_tag.get_key())
        if values_by_se is None:
            values_by_se = []
            self.values_by_searched_tag[searched_tag.get_key()] = values_by_se
        values_by_se.append(searched_value)
    
    def get_value(self, metadata_id: MetadataId) -> SearchedValue:
        """
        Get a single value for the given MetadataId.
        If multiple values exist, returns the first one.
        Returns None if not found.
        """
        key = metadata_id.get_key()
        values = self.values_by_requested_tag.get(key)
        if not values:
            return SearchedValue(None, None)
        return values[0] if len(values) > 0 else SearchedValue(None, None)
    
    def get_all_values(self, metadata_id: MetadataId) -> List[SearchedValue]:
        """
        Get all values for the given MetadataId as a list.
        Returns empty list if not found.
        """
        key = metadata_id.get_key()
        return self.values_by_requested_tag.get(key, [])
    
    def get_single_value(self, metadata_id: MetadataId) -> SearchedValue:
        """
        Get a single value for the given MetadataId.
        Raises ValueError if multiple values exist (use get_value() to get first, or get_all_values() for all).
        Returns None if not found.
        """
        key = metadata_id.get_key()
        values = self.values_by_requested_tag.get(key)
        if not values:
            return SearchedValue(None, None)
        if len(values) > 1:
            raise ValueError(f"Multiple values found for {key}. Use get_all_values() to get all values, or get_value() to get the first.")
        return values[0]

    def get_value_as_timezone(self, metadata_id: MetadataId) -> Optional[datetime.timezone]:
        tz_info_str = self.get_value(metadata_id)
        if tz_info_str.value is None:
            return None
        return metadata_parsers.parse_timezone(tz_info_str.value)

