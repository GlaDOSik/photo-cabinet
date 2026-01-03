from typing import Dict, Set

from initialization.utils.exiftool_web_table import ExiftoolWebTable, ExiftoolWebTableType, ExiftoolTagFieldMapping


class FieldNameMappingValidator:
    def __init__(self):
        self.tables: Dict[str, ExiftoolWebTable] = {}
        self.filtered_rows: Dict[str, Set[ExiftoolTagFieldMapping]] = {}

    def validate_generated_mappings(self):
        for table_name, table in self.tables.items():
            if table.type == ExiftoolWebTableType.STRUCT:
                continue

            self.filtered_rows[table_name] = set()