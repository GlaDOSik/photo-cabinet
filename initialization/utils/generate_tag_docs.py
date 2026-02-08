#!/usr/bin/env python3
import csv
import os
from xml.etree import ElementTree

from exiftool.exif_service import run_command
from exiftool.exiftool_command import ExiftoolCommand

OUTPUT_DIR = "/home/ludek/ProjectData/PhotoCabinet/metadata_csv"

GROUPS_CSV = "groups.csv"
TAGS_CSV = "tags.csv"
VALUES_CSV = "values.csv"

# Uses exiftool to generate base metadata definitions for documenting purpose
def generate_docs():
    xml_data = run_command(ExiftoolCommand.list_supported_metadata())
    root = ElementTree.fromstring(xml_data)

    groups = []
    tags = []
    values = []
    group_tags_by_exif_id = {}

    for table in root.findall("table"):
        namespace = table.attrib["name"]
        g0 = table.attrib["g0"]
        g1 = table.attrib["g1"]
        g2 = table.attrib["g2"]
        groups.append({"namespace": namespace, "g0": g0, "g1": g1, "g2": g2})

        tag_elements = table.findall("tag")
        group_tags_by_exif_id[namespace] = {}
        for tag_el in tag_elements:
            exif_id = tag_el.attrib["id"]
            name = tag_el.attrib["name"]
            group_tags_by_exif_id[namespace][exif_id] = {"name": name, "namespace": namespace}

        for tag_el in tag_elements:
            exif_id = tag_el.attrib["id"]
            name = tag_el.attrib["name"]
            tag_type = tag_el.attrib["type"]
            writable = tag_el.attrib["writable"].lower() == "true"
            desc_el = tag_el.find("desc[@lang='en']")
            description = (desc_el.text or "").strip()
            tag_flags = tag_el.attrib.get("flags") or ""
            is_list = "List" in [f.strip() for f in tag_flags.split(",")]
            parent_struct_id = tag_el.attrib.get("struct")

            parent_tag_name = ""
            parent_tag_namespace = ""
            if parent_struct_id is not None:
                parent = group_tags_by_exif_id[namespace].get(parent_struct_id)
                if parent is not None:
                    parent_tag_name = parent["name"]
                    parent_tag_namespace = parent["namespace"]

            tags.append({
                "group_namespace": namespace,
                "exif_id": exif_id,
                "name": name,
                "type": tag_type,
                "description": description,
                "writable": writable,
                "is_list": is_list,
                "parent_tag_name": parent_tag_name,
                "parent_tag_namespace": parent_tag_namespace,
            })

            for val_el in tag_el.findall(".//values//val[@lang='en']"):
                if val_el.text is None:
                    continue
                value = val_el.text.strip()
                values.append({
                    "tag_namespace": namespace,
                    "tag_name": name,
                    "value": value,
                })

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, GROUPS_CSV), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["namespace", "g0", "g1", "g2"])
        w.writeheader()
        w.writerows(groups)

    with open(os.path.join(OUTPUT_DIR, TAGS_CSV), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "group_namespace", "exif_id", "name", "type", "description",
                "writable", "is_list", "parent_tag_name", "parent_tag_namespace",
            ],
        )
        w.writeheader()
        w.writerows(tags)

    with open(os.path.join(OUTPUT_DIR, VALUES_CSV), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tag_namespace", "tag_name", "value"])
        w.writeheader()
        w.writerows(values)


def main():
    generate_docs()


if __name__ == "__main__":
    main()
