from enum import Enum, auto
from typing import List


class ExiftoolWebTableType(Enum):
    TAG = auto()
    STRUCT = auto()

class ExiftoolWebTableTagType(Enum):
    STRUCT = auto()
    FLAT = auto()

class ExiftoolWebTable:
    def __init__(self):
        self.type: ExiftoolWebTableType = None
        self.rows: List[ExiftoolWebTableRow] = []
        self.generated_mappings: List[ExiftoolTagFieldMapping] = []
        self.g1 = None
        self.name = None

    def add_row(self, name, tag_type, struct_name):
        self.rows.append(ExiftoolWebTableRow(name, tag_type, struct_name))

    def print(self):
        print(f"### {self.type.name} {self.name} {self.g1}")
        for row in self.rows:
            print(f"-- {row.name} - {row.tag_type_raw} - {row.struct_name}")

    def print_mappings(self):
        print(f"### {self.type.name} {self.name} {self.g1}")
        for row in self.generated_mappings:
            print(f"-- {row.generated_tag_name} - {row.field_name}")

    def print_stats(self):
        print(f"### {self.type.name} {self.name} {self.g1} ({len(self.rows)})")

class ExiftoolTagFieldMapping:
    def __init__(self, generated_tag_name: str, field_name: str):
        self.generated_tag_name = generated_tag_name
        self.field_name = field_name

class ExiftoolWebTableRow:
    def __init__(self, name, tag_type, struct_name):
        self.name = name
        self.tag_type_raw = tag_type
        self.tag_types = self._parse_types(tag_type)
        self.struct_name = struct_name

    def _parse_types(self, raw_type: str) -> set:
        tag_types = set()
        if "_" in raw_type:
            tag_types.add(ExiftoolWebTableTagType.FLAT)
        if "struct" in raw_type:
            tag_types.add(ExiftoolWebTableTagType.STRUCT)
        return tag_types

    def is_flat(self):
        return ExiftoolWebTableTagType.FLAT in self.tag_types

    def is_struct(self):
        return ExiftoolWebTableTagType.STRUCT in self.tag_types