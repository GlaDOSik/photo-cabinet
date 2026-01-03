from typing import Dict, List
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from xml.etree import ElementTree

from exiftool.dbe.et_group import ExifToolGroup, find_all as find_all_groups
from exiftool.dbe.et_tag import ExifToolTag, find_by_group as find_tag_by_group
from exiftool.dbe.et_value import ExifToolValue, find_by_tag_ids as find_values_by_tag_ids
import logging

log = logging.getLogger("ExiftoolDataParser")


class ExiftoolDataParser:
    def __init__(self, session: Session):
        self.session = session
        self.existing_groups: Dict[str, List] = dict()
        self.existing_tags: Dict[str, List]
        self.existing_values: Dict[str, List]
        self.tags_for_parent_referencing = []

    def parse_metadata_db(self, xml_data: str):
        self._load_all_groups_from_db()
        root = ElementTree.fromstring(xml_data)
        for table in root.findall("table"):
            exif_group = self._get_or_create_group_namespace(table)
            tags_per_namespace = table.findall("tag")
            self._load_tags_and_values_for_group_from_db(exif_group.id)
            self.tags_for_parent_referencing.clear()
            for tag_element in tags_per_namespace:
                exif_tag = self._get_or_create_tag(tag_element, exif_group.id)
                parent_struct_id = tag_element.attrib.get("struct")
                if parent_struct_id is not None and exif_tag.parent_struct_id is None:
                    self.tags_for_parent_referencing.append((exif_tag, parent_struct_id))
                tag_values = tag_element.findall(".//values//val[@lang='en']")
                for tag_value in tag_values:
                    if tag_value.text is None:
                        continue
                    self._get_or_create_value(tag_value, exif_tag.id)
            self.session.flush()
            self._run_tag_parent_referencing(exif_group.id)
            self._set_deleted_tags_values()
            self.existing_values.clear()
            self.existing_tags.clear()
        self._set_deleted_groups()

    def _load_all_groups_from_db(self):
        all_groups = find_all_groups(self.session)
        for group in all_groups:
            self.existing_groups[group.namespace] = [group, False]

    def _load_tags_and_values_for_group_from_db(self, exif_group_id: UUID):
        existing_tags = find_tag_by_group(self.session, exif_group_id)
        self.existing_tags = {}
        self.existing_values = {}
        existing_tags_ids = []
        for existing_tag in existing_tags:
            existing_tags_ids.append(existing_tag.id)
            self.existing_tags[str(exif_group_id) + existing_tag.exif_id] = [existing_tag, False]
        existing_values = find_values_by_tag_ids(self.session, existing_tags_ids)
        for existing_value in existing_values:
            self.existing_values[str(existing_value.tag_id) + existing_value.value] = [existing_value, False]

    def _run_tag_parent_referencing(self, group_id: UUID):
        for element in self.tags_for_parent_referencing:
            parent_exif_tag = self.existing_tags.get(str(group_id) + element[1])
            if parent_exif_tag is not None:
                element[0].parent_struct_id = parent_exif_tag[0].id

    def _get_or_create_group_namespace(self, table):
        namespace = table.attrib["name"]
        exif_group = self.existing_groups.get(namespace)
        if exif_group is not None:
            exif_group[1] = True
            return exif_group[0]
        else:
            exif_group = ExifToolGroup()
            exif_group.id = uuid4()
            exif_group.g0 = table.attrib["g0"]
            exif_group.g1 = table.attrib["g1"]
            exif_group.g2 = table.attrib["g2"]
            exif_group.namespace = table.attrib["name"]
            self.session.add(exif_group)
            self.session.flush()
            return exif_group

    def _get_or_create_tag(self, tag_element, group_id: UUID):
        exif_id = tag_element.attrib["id"]
        exif_tag = self.existing_tags.get(str(group_id) + exif_id)
        if exif_tag is not None:
            exif_tag[1] = True
            return exif_tag[0]
        else:
            exif_tag = ExifToolTag()
            exif_tag.id = uuid4()
            exif_tag.group_id = group_id
            exif_tag.exif_id = exif_id
            exif_tag.name = tag_element.attrib["name"]
            exif_tag.type = tag_element.attrib["type"]
            exif_tag.writable = tag_element.attrib["writable"].lower() == "true"
            exif_tag.description = tag_element.find("desc[@lang='en']").text
            tag_flags = tag_element.attrib.get("flags")
            if tag_flags is not None:
                flag_split = tag_flags.split(",")
                for flag in flag_split:
                    if flag == "List":
                        exif_tag.is_list = True
            self.existing_tags[str(group_id) + exif_id] = [exif_tag, True] # we need it for parent referencing
            self.session.add(exif_tag)
            return exif_tag

    def _get_or_create_value(self, value_element, tag_id: UUID):
        value = value_element.text
        exif_value = self.existing_values.get(str(tag_id) + value)
        if exif_value is not None:
            exif_value[1] = True
            return exif_value[0]
        else:
            exif_value = ExifToolValue()
            exif_value.id = uuid4()
            exif_value.tag_id = tag_id
            exif_value.value = value
            self.session.add(exif_value)
            return exif_value

    def _set_deleted_groups(self):
        for key, value in self.existing_groups.items():
            if value[1] == False:
                value[0].deleted = True

    def _set_deleted_tags_values(self):
        for key, value in self.existing_values.items():
            if value[1] == False:
                value[0].deleted = True
        for key, value in self.existing_tags.items():
            if value[1] == False:
                value[0].deleted = True