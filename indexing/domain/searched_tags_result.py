import datetime
from typing import Dict, Any, List, Optional

from domain.metadata import metadata_parsers
from domain.metadata.metadata_id import MetadataId


class SearchedTagsResult:
    def __init__(self):
        self.searched_tags: List[MetadataId] = []
        # Store lists of values to handle multiple matches (e.g., from arrays)
        self.searched_values: Dict[str, List[Any]] = dict()
    
    def get_value(self, metadata_id: MetadataId) -> Any:
        """
        Get a single value for the given MetadataId.
        If multiple values exist, returns the first one.
        Returns None if not found.
        """
        key = metadata_id.get_key()
        values = self.searched_values.get(key)
        if not values:
            return None
        return values[0] if len(values) > 0 else None
    
    def get_all_values(self, metadata_id: MetadataId) -> List[Any]:
        """
        Get all values for the given MetadataId as a list.
        Returns empty list if not found.
        """
        key = metadata_id.get_key()
        return self.searched_values.get(key, [])
    
    def get_single_value(self, metadata_id: MetadataId) -> Any:
        """
        Get a single value for the given MetadataId.
        Raises ValueError if multiple values exist (use get_value() to get first, or get_all_values() for all).
        Returns None if not found.
        """
        key = metadata_id.get_key()
        values = self.searched_values.get(key)
        if not values:
            return None
        if len(values) > 1:
            raise ValueError(f"Multiple values found for {key}. Use get_all_values() to get all values, or get_value() to get the first.")
        return values[0]

    def get_value_as_timezone(self, metadata_id: MetadataId) -> Optional[datetime.timezone]:
        tz_info_str = self.get_value(metadata_id)
        if tz_info_str is None:
            return None
        return metadata_parsers.parse_timezone(tz_info_str)