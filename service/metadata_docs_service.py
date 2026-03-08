from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from domain.metadata.metadata_id import MetadataId, PathStruct
from root import ROOT_DIR
from dbe.docs.docs_et_tag import find_by_tag_name as find_tag_docs_by_tag_name, \
    find_by_field_name as find_tag_docs_by_field_name, DocsExifToolTag


def _load_tag_docs_template() -> str:
    path = Path(ROOT_DIR) / "docs" / "metadata" / "tag_docs_template.md"
    return path.read_text()


tag_docs_template: str = _load_tag_docs_template()


def search_docs(session: Session, metadata_id: MetadataId, tag_value) -> Optional[str]:
    if len(metadata_id.path) > 0 and metadata_id.tag_name is None:  # only structs in path
        return None
    elif len(metadata_id.path) > 0 and metadata_id.tag_name is not None:  # it is tag with path
        return None
    elif len(metadata_id.path) == 0 and metadata_id.tag_name is not None:  # it is tag without path
        tags = find_tag_docs_by_tag_name(session, metadata_id.tag_name)
        matched = _filter_tags_by_groups(tags, metadata_id)
        return _populate_tag_template(matched, metadata_id)
    return None

def _walk_path(session: Session, metadata_id: MetadataId):
    for path_part in metadata_id.path:
        if isinstance(path_part, PathStruct):
            docs_tags: [DocsExifToolTag] = find_tag_docs_by_field_name(session, path_part.struct_name)

def _populate_tag_template(tag_docs: DocsExifToolTag, metadata_id: MetadataId) -> str:
    description = "" if tag_docs is None or tag_docs.description is None else tag_docs.description
    return (
        tag_docs_template
        .replace("<tag_name>", metadata_id.tag_name)
        .replace("<description>", description + "\n")
        .replace("<g0>", metadata_id.group_0)
        .replace("<g1>", "-" if metadata_id.group_1 is None else metadata_id.group_1)
    )


def _filter_tags_by_groups(tags: [DocsExifToolTag], metadata_id: MetadataId) -> Optional[DocsExifToolTag]:
    g0_matched_tags = []
    g0_g1_matched_tags = []
    for tag in tags:
        g0_matched = tag.exif_group.g0 == metadata_id.group_0
        g1_matched = metadata_id.group_1 is not None and tag.exif_group.g1 == metadata_id.group_1
        if g0_matched and g1_matched:
            g0_g1_matched_tags.append(tag)
        elif g0_matched:
            g0_matched_tags.append(tag)
    if len(g0_g1_matched_tags) == 1:
        return g0_g1_matched_tags[0]
    elif len(g0_matched_tags) == 1:
        return g0_matched_tags[0]
    else:
        return None