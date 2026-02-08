import re
from typing import List, Optional, Union

from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_group_1 import MetadataGroup1
from domain.metadata.metadata_name import MetadataName


class PathStruct:
    def __init__(self, struct_name: str):
        self.struct_name: str = struct_name

    def to_dict(self):
        return self.struct_name

    def __str__(self):
        return self.struct_name

    def __eq__(self, other):
        if not isinstance(other, PathStruct):
            return NotImplemented
        return self.struct_name == other.struct_name

class PathArray:
    def __init__(self, array_name: str, array_index: int):
        self.array_name: str = array_name
        self.array_index: int = array_index

    def to_dict(self):
        return {"array": self.array_name, "idx": self.array_index}

    def __str__(self):
        return f"{self.array_name}.{str(self.array_index)}"

    def __eq__(self, other):
        if not isinstance(other, PathArray):
            return NotImplemented
        return self.array_name == other.array_name and self.array_index == other.array_index


def parse_path(path_str: Optional[str]) -> List[PathStruct | PathArray]:
    """Parse path string like 'Look.Parameters' or 'TestArray[0].NestedKey' into path objects."""
    if not path_str or not path_str.strip():
        return []
    list_index_pattern = re.compile(r"^(.+)\[(\d+)\]$")
    result: List[PathStruct | PathArray] = []
    for part in path_str.split("."):
        part = part.strip()
        if not part:
            continue
        match = list_index_pattern.match(part)
        if match:
            result.append(PathArray(match.group(1), int(match.group(2))))
        else:
            result.append(PathStruct(part))
    return result


class MetadataId:
    def __init__(self, metadata_group_0: str, metadata_group_1: Optional[str], metadata_name: Optional[str],
                 path: Union[str, List[PathStruct | PathArray], None] = None):
        self.group_0: str = metadata_group_0
        self.group_1: str = metadata_group_1
        self.tag_name: str = metadata_name
        # Optional path to specify nested structure, e.g., "Look.Parameters"
        if path is None:
            self.path: List[PathStruct | PathArray] = []
        elif isinstance(path, str):
            self.path = parse_path(path)
        else:
            self.path = list(path)

    def _full_tag_path(self) -> str:
        tag_path = ".".join(str(p) for p in self.path)
        return self.tag_name if tag_path == "" else f"{tag_path}.{self.tag_name}"

    def get_key(self):
        group_1_key = self.group_1 if self.group_1 else ""
        return f"{self.group_0}:{group_1_key}:{self._full_tag_path()}"

    @staticmethod
    def of(metadata_group_0: MetadataGroup0, metadata_group_1: MetadataGroup1 | None, metadata_name: MetadataName | None):
        g1_text = None if metadata_group_1 is None else metadata_group_1.metadata_name
        metadata_name_text = None if metadata_name is None else metadata_name.metadata_name
        return MetadataId(metadata_group_0.metadata_name, g1_text, metadata_name_text)

    def get_glom_path(self):
        return f"{self.get_glom_path_g1()}.{self._full_tag_path()}"

    # Path up to g1 (or g0 is not g1)
    def get_glom_path_g1(self):
        g1_part = "tags" if self.group_1 is None else f"g1.{self.group_1}"
        return f"{self.group_0}.{g1_part}"

    def to_dict(self):
        d = {"g0": self.group_0, "tag_name": self.tag_name}
        if self.group_1 is not None:
            d["g1"] = self.group_1
        if self.path:
            d["path"] = [p.to_dict() for p in self.path]
        return d

    @staticmethod
    def from_dict(d: dict) -> "MetadataId":
        """Deserialize from dict produced by to_dict()."""
        path_raw = d.get("path")
        if path_raw:
            path = [
                PathStruct(p) if isinstance(p, str) else PathArray(p["array"], p["idx"])
                for p in path_raw
            ]
        else:
            path = None
        return MetadataId(d.get("g0"), d.get("g1"), d.get("tag_name"), path)

    def __eq__(self, other):
        if not isinstance(other, MetadataId):
            return NotImplemented
        return (self.group_0 == other.group_0 and
                self.group_1 == other.group_1 and
                self.tag_name == other.tag_name and
                self.path == other.path)