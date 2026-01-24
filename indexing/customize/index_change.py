from abc import ABC, abstractmethod
from typing import Dict

from domain.metadata.metadata_id import MetadataId
from indexing.domain.index_change_status import IndexChangeStatus
from indexing.domain.index_change_type import IndexChangeType


class IndexChange(ABC):
    def __init__(self, change_type: IndexChangeType, metadata_id: MetadataId):
        self.metadata_id: MetadataId = metadata_id
        self.change_type: IndexChangeType = change_type

    @abstractmethod
    def execute_on_index(self, exif_json: Dict):
        pass

    @abstractmethod
    def check_status(self, exif_json: Dict) -> IndexChangeStatus:
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        pass

    def base_to_dict(self):
        base = {"metadata_id": {"g0": self.metadata_id.group_0, "tag_name": self.metadata_id.tag_name},
                "type": self.change_type.name}
        if self.metadata_id.group_1 is not None:
            base["metadata_id"]["g1"] = self.metadata_id.group_1
        if self.metadata_id.path is not None:
            base["metadata_id"]["path"] = self.metadata_id.path
        return base

    @staticmethod
    def from_dict(input_dict: Dict):
        change_type: IndexChangeType = IndexChangeType[input_dict.get("type")]
        metadata_id_dict = input_dict.get("metadata_id")
        g0 = metadata_id_dict.get("g0")
        g1 = metadata_id_dict.get("g1")
        tag_name = metadata_id_dict.get("tag_name")
        path = metadata_id_dict.get("path")
        metadata_id = MetadataId(g0, g1, tag_name, path)
        
        if change_type == IndexChangeType.CREATE:
            value = input_dict.get("new_value")
            from indexing.customize.create_change import CreateChange
            return CreateChange(value, metadata_id)
        
        raise ValueError(f"Unknown change type: {change_type}")