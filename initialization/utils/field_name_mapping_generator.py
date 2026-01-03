from typing import Dict, List

from initialization.utils.exiftool_web_table import ExiftoolWebTable, ExiftoolWebTableRow, ExiftoolTagFieldMapping, \
    ExiftoolWebTableType


class FieldNameMappingGenerator:
    def __init__(self):
        self.tables: Dict[str, ExiftoolWebTable] = {}

    def generate_flat_tag_names(self):
        for table_name, table in self.tables.items():
            if table.type == ExiftoolWebTableType.STRUCT:
                continue
            self._process_structure(table, False, table.rows, "")

    def _process_structure(self, table: ExiftoolWebTable, is_nested, table_rows: List[ExiftoolWebTableRow], parent_name):
        for row in table_rows:
            current_name = parent_name + row.name
            if row.is_struct():
                referenced_table = self.tables.get(row.struct_name)
                if referenced_table is None:
                    raise Exception(f"No table {row.struct_name} found")
                # We want struct because there are tags for structs
                table.generated_mappings.append(ExiftoolTagFieldMapping(current_name, row.name))
                # But next level will try to use overridden name
                # name_override = FIELD_NAME_HIERARCHY_OVERRIDE.get(tag_table_name + "-" + current_tag_field_name)
                # if name_override is not None:
                #     current_tag_field_name = name_override
                self._process_structure(table, True, referenced_table.rows, current_name)
            elif is_nested is True:
                # direct_override = FIELD_NAME_DIRECT_OVERRIDE.get(tag_table_name + "-" + current_tag_field_name)
                # if direct_override is not None:
                #     current_tag_field_name = direct_override
                table.generated_mappings.append(ExiftoolTagFieldMapping(current_name, row.name))

    def print(self, table_name):
        table = self.tables.get(table_name)
        table.print_mappings()