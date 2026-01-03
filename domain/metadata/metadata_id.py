from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_group_1 import MetadataGroup1
from domain.metadata.metadata_name import MetadataName


class MetadataId:
    def __init__(self, metadata_group_0: str, metadata_group_1: str | None, metadata_name: str, path: str | None = None):
        self.group_0: str = metadata_group_0
        self.group_1: str = metadata_group_1
        self.tag_name: str = metadata_name
        # Optional path to specify nested structure, e.g., "Look.Parameters"
        self.path: str | None = path

    def get_key(self):
        path_part = f"{self.path}." if self.path else ""
        return f"{self.group_0}:{self.group_1}:{path_part}{self.tag_name}"

    @staticmethod
    def of(metadata_group_0: MetadataGroup0, metadata_group_1: MetadataGroup1 | None, metadata_name: MetadataName):
        g1_text = None if metadata_group_1 is None else metadata_group_1.metadata_name
        return MetadataId(metadata_group_0.metadata_name, g1_text, metadata_name.metadata_name)

    def __eq__(self, other):
        if not isinstance(other, MetadataId):
            return NotImplemented
        return (self.group_0 == other.group_0 and
                self.group_1 == other.group_1 and
                self.tag_name == other.tag_name and
                self.path == other.path)