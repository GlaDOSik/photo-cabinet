import re
from typing import Dict

import requests
from bs4 import BeautifulSoup

from initialization.utils.exiftool_web_table import ExiftoolWebTable, ExiftoolWebTableType

XMP_URL = "https://exiftool.org/TagNames/XMP.html"


class ExiftoolWebTableParser:
    def __init__(self):
        self.current_table: ExiftoolWebTable = None
        self.tables: Dict[str, ExiftoolWebTable] = {}

    def _create_tags_table(self, tag_table_name: str):
        """Placeholder method for XMP xxxxx Tags format."""
        # print(f"Tags namespace: {tag_table_name}")
        self.current_table = ExiftoolWebTable()
        self.current_table.name = tag_table_name
        self.current_table.type = ExiftoolWebTableType.TAG
        self.tables[tag_table_name] = self.current_table


    def _create_struct_table(self, struct_name: str):
        """Placeholder method for XMP xxxxx Struct format."""
        # print(f"Struct namespace: {struct_name}")
        self.current_table = ExiftoolWebTable()
        self.current_table.name = struct_name
        self.current_table.type = ExiftoolWebTableType.STRUCT
        self.tables[struct_name] = self.current_table

    def _assign_family_group(self, group_name: str):
        """Placeholder method for family group names."""
        self.current_table.g1 = group_name


    def _create_table_row(self, col1: str, col2: str, col3: str):
        """Placeholder method for table row data."""
        if self.current_table is None:
            return
        # Skip table header
        if (col1 == "Tag Name" or col1 == "Field Name") and col2 == "Writable":
            return
        if col3.endswith(" Struct"):
            col3 = col3.replace(" Struct", "")
        else:
            col3 = None
        self.current_table.add_row(col1, col2, col3)

    # Parses the html to tag tables and struct tables
    def parse_xmp_html(self):
        """Parse XMP.html and extract tag information."""
        # Fetch the HTML content
        response = requests.get(XMP_URL)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get body and loop through all elements in order
        body = soup.find('body')
        if not body:
            return

        # Loop through all elements in the body in order of appearance
        for element in body.descendants:
            # Skip if it's not a Tag object (e.g., NavigableString)
            if not hasattr(element, 'name'):
                continue

            # Check for h2 tags
            if element.name == 'h2':
                a_tag = element.find('a')
                if a_tag:
                    content = a_tag.get_text(strip=True)
                    # Check for "XMP xxxxx Tags" format
                    match_tags = re.match(r'XMP\s+(.+?)\s+Tags$', content)
                    if match_tags:
                        namespace = match_tags.group(1)
                        self._create_tags_table(namespace)
                    # Check for "XMP xxxxx Struct" format
                    match_struct = re.match(r'XMP\s+(.+?)\s+Struct$', content)
                    if match_struct:
                        namespace = match_struct.group(1)
                        self._create_struct_table(namespace)

            # Check for p tags
            elif element.name == 'p':
                content = element.get_text()
                # Match pattern: "These tags belong to the ExifTool XMP-xxxxx family 1 group."
                match = re.search(r'These tags belong to the ExifTool\s+(XMP-[^\s]+)\s+family 1 group\.', content)
                if match:
                    group_name = match.group(1)
                    self._assign_family_group(group_name)

            # Check for table with class="frame"
            elif element.name == 'table' and element.get('class') and 'frame' in element.get('class'):
                # Find inner table with class="inner"
                inner_table = element.find('table', class_='inner')
                if inner_table:
                    # Check if it has 3 columns
                    rows = inner_table.find_all('tr')
                    for row in rows:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) == 3:
                            # Get content of first two columns directly
                            col1_text = cols[0].get_text(strip=True)
                            col2_text = cols[1].get_text(strip=True)

                            # Get content of a tag in third column
                            col3_a = cols[2].find('a')
                            if col3_a:
                                col3_text = col3_a.get_text(strip=True)
                            else:
                                col3_text = cols[2].get_text(strip=True)

                            self._create_table_row(col1_text, col2_text, col3_text)

    def print(self, table_name):
        table = self.tables.get(table_name)
        table.print()

    def print_stats(self):
        print("TABLE NAMES: " + ", ".join(self.tables.keys()))
        for table in self.tables.values():
            table.print_stats()