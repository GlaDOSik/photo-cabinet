import re
from typing import List, Optional

from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_group_1 import MetadataGroup1
from domain.metadata.metadata_name import MetadataName
from vial import putils

TAG_ID_DELIMITER = "@"


class MetadataId:
    def __init__(self, metadata_group_0: str, metadata_group_1: Optional[str], metadata_name: Optional[str],
                 metadata_id: Optional[str] = None, path: str|None = None):
        self.group_0: str = metadata_group_0
        self.group_1: str = metadata_group_1
        # tag id unique for group_0 - preferable over tag_name and path
        self.tag_id: str = metadata_id
        self.tag_name: str = metadata_name
        self.path = path

    def get_key(self):
        group_1_key = putils.coalesce(self.group_1, "")
        path_key = putils.coalesce(self.group_1, "")
        name_key = putils.coalesce(self.tag_name, "")
        id_key = putils.coalesce(self.tag_id, "")
        return f"{self.group_0}:{group_1_key}:{path_key}:{name_key}:{id_key}"

    @staticmethod
    def of(metadata_group_0: MetadataGroup0, metadata_group_1: MetadataGroup1 | None,
           metadata_name: MetadataName | None, tag_id: str | None = None):
        g1_text = None if metadata_group_1 is None else metadata_group_1.metadata_name
        metadata_name_text = None if metadata_name is None else metadata_name.metadata_name
        return MetadataId(metadata_group_0.metadata_name, g1_text, metadata_name_text, metadata_id=tag_id)

    def _get_tag_json_path(self, strict_path: bool) -> str:
        tag_name = putils.coalesce(self.tag_name, ".*")
        tag_id = putils.coalesce(self.tag_id, ".*")
        tag_pattern = f"{tag_name}{TAG_ID_DELIMITER}{tag_id}"
        tag_specifier = f"[?match(#, '{tag_pattern}')]"

        if self.path is None and not strict_path:
            path_part = ".."  # TODO
        elif self.path is None:
            path_part = ""
        else:
            segments = [s for s in self.path.strip(".").split(".") if s]
            path_part = "".join(f"[?match(#, '{seg}{TAG_ID_DELIMITER}.*')]" for seg in segments)

        return f"{path_part}{tag_specifier}"

    def _get_group_json_paths(self, strict_g1: bool) -> list[str]:
        """
        Return JSON path(s) within groups.
        :param strict_g1: If false, search in all g1 groups and also in g0 tags. If true, only within g0.tags.
        :return: List of JSON path prefixes.
        """
        if self.group_1 is None and not strict_g1:
            return [f"$.{self.group_0}.tags", f"$.{self.group_0}.g1.*"]
        elif self.group_1 is None:
            return [f"$.{self.group_0}.tags"]
        else:
            return [f"$.{self.group_0}.g1.{self.group_1}"]

    def get_json_paths(self, strict_g1: bool = True, strict_path: bool = True) -> list[str]:
        tag_part = self._get_tag_json_path(strict_path)
        return [f"{group_path}{tag_part}" for group_path in self._get_group_json_paths(strict_g1)]

    @staticmethod
    def from_json_path(json_path: str) -> "MetadataId":
        segments = re.findall(r"\['([^']+)'\]", json_path)
        # segments: [group_0, ('g1'|'tags'), [group_1,] [path...,] tag_name@tag_id]
        group_0 = segments[0]
        tag_segment = segments[-1]
        tag_name, tag_id = tag_segment.split(TAG_ID_DELIMITER, 1) if TAG_ID_DELIMITER in tag_segment else (tag_segment, None)

        if segments[1] == "g1":
            group_1 = segments[2]
            path_segments = segments[3:-1]
        else:  # 'tags'
            group_1 = None
            path_segments = segments[2:-1]

        path = "." + ".".join(path_segments) if path_segments else None
        return MetadataId(group_0, group_1, tag_name, metadata_id=tag_id, path=path)

    def to_dict(self):
        d = {"g0": self.group_0}
        putils.add_if_not_none(d, "g1", self.group_1)
        putils.add_if_not_none(d, "path", self.path)
        putils.add_if_not_none(d, "tag_name", self.tag_name)
        putils.add_if_not_none(d, "tag_id", self.tag_id)
        return d

    @staticmethod
    def from_dict(d: dict) -> "MetadataId":
        """Deserialize from dict produced by to_dict()."""
        return MetadataId(d.get("g0"), d.get("g1"), d.get("tag_name"), d.get("path"))

    def __eq__(self, other):
        if not isinstance(other, MetadataId):
            return NotImplemented
        return (self.group_0 == other.group_0 and
                self.group_1 == other.group_1 and
                self.tag_name == other.tag_name and
                self.path == other.path and
                self.tag_id == other.tag_id)