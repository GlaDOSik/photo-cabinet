from typing import Dict, Any

from glom import glom, PathAccessError

from domain.metadata.metadata_id import MetadataId
from indexing.customize.index_change import IndexChange
from indexing.domain.index_change_status import IndexChangeStatus
from indexing.domain.index_change_type import IndexChangeType
from indexing import metadata_indexing_service


class CreateChange(IndexChange):
    def __init__(self, value: str, metadata_id: MetadataId):
        super().__init__(IndexChangeType.CREATE, metadata_id)
        self.value = value

    def execute_on_index(self, exif_json: Dict):
        pass

    def check_status(self, exif_json: Dict) -> IndexChangeStatus:
        try:
            result = metadata_indexing_service.search_index_value(exif_json, self.metadata_id)
        except PathAccessError as ex:
            return IndexChangeStatus.NOT_APPLIED
        if result == self.value:
            return IndexChangeStatus.APPLIED
        return IndexChangeStatus.NOT_APPLIED_DIFF_VALUE

    def to_dict(self) -> Dict:
        base_dict = self.base_to_dict()
        base_dict["new_value"] = self.value
        return base_dict