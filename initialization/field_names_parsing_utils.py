import requests
from bs4 import BeautifulSoup
import re

from initialization.utils.exiftool_web_table_parser import ExiftoolWebTableParser
from initialization.utils.field_name_mapping_generator import FieldNameMappingGenerator

# Flat tag name is constructed from field names by appending it in recursion util the structure is iterated
# But sometimes, the parent struct name differs than inner struct or tag name
# Example NO OVERRIDE Colorants: {ColorantsA: value} OVERRIDE Colorants: {ColorantA: value}
FIELD_NAME_HIERARCHY_OVERRIDE = {"xmpTPg-Colorants": "Colorant",
                                 "xmpTPg-Fonts": "",
                                 "xmpTPg-SwatchGroupsColorants": "SwatchColorant"}
FIELD_NAME_DIRECT_OVERRIDE = {"xmpTPg-Composite": "FontComposite",
                              "xmpTPg-VersionString": "FontVersion",
                              "xmpTPg-SwatchGroupsGroupType": "SwatchGroupType",
                              "xmpTPg-SwatchGroupsGroupName": "SwatchGroupName"}

if __name__ == '__main__':
    parser = ExiftoolWebTableParser()
    parser.parse_xmp_html()
    # parser.print("ACDSeeRegions")

    mapping_generator = FieldNameMappingGenerator()
    mapping_generator.tables = parser.tables
    mapping_generator.generate_flat_tag_names()
    mapping_generator.print("ACDSeeRegions")


