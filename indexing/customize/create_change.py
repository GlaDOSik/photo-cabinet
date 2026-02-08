from typing import Dict, Any

from glom import glom, PathAccessError

from domain.metadata.metadata_id import MetadataId
from indexing.customize.index_change import IndexChange
from indexing.domain.index_change_status import IndexChangeValidationStatus
from indexing.domain.index_change_type import IndexChangeType
from indexing.metadata_indexing_repository import search_index_value, set_index_value


class CreateChange(IndexChange):
    def __init__(self, value: str, metadata_id: MetadataId):
        super().__init__(IndexChangeType.CREATE, metadata_id)
        self.value = value

    def execute_on_index(self, effective_json: Dict):
        set_index_value(effective_json, self.metadata_id, self.value)

    def validate(self, exif_json: Dict) -> IndexChangeValidationStatus:
        try:
            result = search_index_value(exif_json, self.metadata_id)
        except PathAccessError as ex:
            return IndexChangeValidationStatus.NOT_CREATED
        if result == self.value:
            return IndexChangeValidationStatus.CREATED
        return IndexChangeValidationStatus.EXISTS_DIFF_VALUE

    def to_dict(self) -> Dict:
        base_dict = self.base_to_dict()
        base_dict["new_value"] = self.value
        return base_dict