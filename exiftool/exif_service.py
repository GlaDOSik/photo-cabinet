import csv
import os
import subprocess
from uuid import uuid4

from sqlalchemy.orm import Session

from dbe.app_data import get_app_data_val, set_app_data_value
from domain.app_data_field import AppDataField
from exiftool.dbe.docs_et_group import DocsExifToolGroup
from exiftool.dbe.docs_et_tag import DocsExifToolTag
from exiftool.dbe.docs_et_value import DocsExifToolValue
from exiftool.exiftool_command import ExiftoolCommand

## Service for working with Exiftool

METADATA_DOCS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "initialization", "metadata_docs")
)


def _parse_bool(s: str) -> bool:
    return str(s).strip().lower() in ("1", "true", "yes", "on")


def load_metadata_docs_from_csv(session: Session) -> None:
    """Load metadata definitions from initialization/metadata_docs CSVs into DocsExifToolGroup, DocsExifToolTag, DocsExifToolValue."""
    groups_path = os.path.join(METADATA_DOCS_DIR, "groups.csv")
    tags_path = os.path.join(METADATA_DOCS_DIR, "tags.csv")
    struct_fields_path = os.path.join(METADATA_DOCS_DIR, "struct_fields.csv")
    tag_descriptions_path = os.path.join(METADATA_DOCS_DIR, "tag_descriptions.csv")
    values_path = os.path.join(METADATA_DOCS_DIR, "values.csv")

    # TODO this takes a lot of time - around 70 seconds. Can we improve the performance? Would be also worth running analyze and full vacuum
    # Because without it, the table size doubles
    session.query(DocsExifToolValue).filter_by(user_created=False).delete(synchronize_session=False)
    session.query(DocsExifToolTag).filter_by(user_created=False).delete(synchronize_session=False)
    session.query(DocsExifToolGroup).filter_by(user_created=False).delete(synchronize_session=False)
    session.flush()

    namespace_to_group = {}
    with open(groups_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            g = DocsExifToolGroup()
            g.id = uuid4()
            g.namespace = row["namespace"]
            g.g0 = row["g0"]
            g.g1 = row["g1"]
            g.g2 = row["g2"]
            g.user_created = False
            session.add(g)
            namespace_to_group[g.namespace] = g
    session.flush()

    tag_key_to_tag = {}
    tag_to_parent_key = []
    with open(tags_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns = row["group_namespace"]
            group = namespace_to_group.get(ns)
            if group is None:
                continue
            t = DocsExifToolTag()
            t.id = uuid4()
            t.group_id = group.id
            t.exif_id = row["exif_id"]
            t.name = row["name"]
            t.type = row["type"]
            t.description = (row.get("description") or "").strip()
            t.writable = _parse_bool(row.get("writable", "false"))
            t.is_list = _parse_bool(row.get("is_list", "false"))
            t.user_created = False
            session.add(t)
            key = (ns, row["name"])
            tag_key_to_tag[key] = t
            pn = (row.get("parent_tag_namespace") or "").strip()
            pname = (row.get("parent_tag_name") or "").strip()
            if pn and pname:
                tag_to_parent_key.append((t, (pn, pname)))
    session.flush()

    if os.path.isfile(struct_fields_path):
        with open(struct_fields_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["group_namespace"], row["tag_name"])
                tag = tag_key_to_tag.get(key)
                if tag is not None:
                    tag.field_name = (row.get("field_name") or "").strip() or None

    if os.path.isfile(tag_descriptions_path):
        with open(tag_descriptions_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["group_namespace"], row["tag_name"])
                tag = tag_key_to_tag.get(key)
                if tag is not None:
                    tag.description = (row.get("description") or "").strip()

    for tag, parent_key in tag_to_parent_key:
        parent = tag_key_to_tag.get(parent_key)
        if parent is not None:
            tag.parent_struct_id = parent.id
    session.flush()

    if os.path.isfile(values_path):
        with open(values_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["tag_namespace"], row["tag_name"])
                tag = tag_key_to_tag.get(key)
                if tag is None:
                    continue
                v = DocsExifToolValue()
                v.id = uuid4()
                v.tag_id = tag.id
                v.value = (row.get("value") or "").strip()
                v.user_created = False
                session.add(v)
    session.flush()


def run_command(exiftool_command: ExiftoolCommand) -> str:
    try:
        result = subprocess.run(
            exiftool_command.get_command(),
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise TimeoutError("exiftool tags list timed out")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get exiftool tags: {e.stderr}")