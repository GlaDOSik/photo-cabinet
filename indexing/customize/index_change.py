from abc import ABC, abstractmethod
from typing import Dict

from domain.metadata.metadata_id import MetadataId
from indexing.domain.index_change_status import IndexChangeValidationStatus
from indexing.domain.index_change_type import IndexChangeType


class IndexChange(ABC):
    def __init__(self, change_type: IndexChangeType, metadata_id: MetadataId):
        self.metadata_id: MetadataId = metadata_id
        self.change_type: IndexChangeType = change_type

    @abstractmethod
    def execute_on_index(self, exif_json: Dict):
        pass

    @abstractmethod
    def validate(self, exif_json: Dict) -> IndexChangeValidationStatus:
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        pass

    def base_to_dict(self):
        base = {"metadata_id": self.metadata_id.to_dict(), "type": self.change_type.name}
        return base

    @staticmethod
    def from_dict(input_dict: Dict):
        change_type: IndexChangeType = IndexChangeType[input_dict.get("type")]
        metadata_id = MetadataId.from_dict(input_dict.get("metadata_id", {}))
        
        if change_type == IndexChangeType.CREATE:
            value = input_dict.get("new_value")
            from indexing.customize.create_change import CreateChange
            return CreateChange(value, metadata_id)
        
        raise ValueError(f"Unknown change type: {change_type}")