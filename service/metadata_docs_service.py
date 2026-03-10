import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from domain.metadata.metadata_id import MetadataId
from vial import putils

logger = logging.getLogger(__name__)
from root import ROOT_DIR
from dbe.docs.docs_et_tag import (
    find_by_tag_id as find_tag_docs_by_tag_id,
    find_by_tag_name as find_tag_docs_by_tag_name,
    find_by_field_name_and_parent as find_tag_docs_by_field_name_and_parent,
    find_by_tag_name_and_parent as find_tag_docs_by_tag_name_and_parent,
    DocsExifToolTag,
)


def _load_tag_docs_template() -> str:
    path = Path(ROOT_DIR) / "docs" / "metadata" / "tag_docs_template.md"
    return path.read_text()


tag_docs_template: str = _load_tag_docs_template()

# TODO - support docs only for g0 and g1 (when tag is not defined)
def search_docs(session: Session, metadata_id: MetadataId, tag_value) -> Optional[str]:
    if tag_value is not None:
        return None  # TODO tag value search not implemented yet
    tag_docs = _search_tag_docs(session, metadata_id)
    return _populate_tag_template(tag_docs, metadata_id)


def _search_tag_docs(session: Session, metadata_id: MetadataId) -> Optional[DocsExifToolTag]:
    if metadata_id.tag_id is not None:
        tags = find_tag_docs_by_tag_id(session, metadata_id.tag_id)
        result = _filter_tags_by_groups(tags, metadata_id)
        if result is not None:
            return result

    if metadata_id.path is not None:
        return _walk_path(session, metadata_id)

    if metadata_id.tag_name is not None:
        tags = find_tag_docs_by_tag_name(session, metadata_id.tag_name)
        return _filter_tags_by_groups(tags, metadata_id)

    return None


def _tag_dump(tag: Optional[DocsExifToolTag]) -> str:
    if tag is None:
        return "None"
    return (
        f"id={tag.id} exif_id={tag.exif_id} name={tag.name} "
        f"field_name={tag.field_name} parent_struct_id={tag.parent_struct_id} "
        f"type={tag.type} writable={tag.writable} is_list={tag.is_list} "
        f"user_created={tag.user_created} description={tag.description!r}"
    )


def _walk_path(session: Session, metadata_id: MetadataId) -> Optional[DocsExifToolTag]:
    segments = [s for s in metadata_id.path.strip(".").split(".") if s]
    prev_tag: Optional[DocsExifToolTag] = None

    for segment in segments:
        parent_id = prev_tag.id if prev_tag else None
        found = _search_by_field_or_name(session, segment, parent_id, metadata_id)
        if found is None:
            logger.debug("Path walk failed at segment '%s', last found: %s", segment, _tag_dump(prev_tag))
            return None
        prev_tag = found

    if metadata_id.tag_name is None:
        return None

    parent_id = prev_tag.id if prev_tag else None
    result = _search_by_field_or_name(session, metadata_id.tag_name, parent_id, metadata_id)
    if result is None:
        logger.debug("Path walk failed at final tag '%s', last found: %s", metadata_id.tag_name, _tag_dump(prev_tag))
    return result


def _search_by_field_or_name(
    session: Session, name: str, parent_struct_id: Optional[UUID], metadata_id: MetadataId
) -> Optional[DocsExifToolTag]:
    tags = find_tag_docs_by_field_name_and_parent(session, name, parent_struct_id)
    result = _filter_tags_by_groups(tags, metadata_id)
    if result is None:
        tags = find_tag_docs_by_tag_name_and_parent(session, name, parent_struct_id)
        result = _filter_tags_by_groups(tags, metadata_id)
    return result


def _populate_tag_template(tag_docs: DocsExifToolTag, metadata_id: MetadataId) -> str:
    tag_name = metadata_id.tag_name
    tag_id = ""
    description = ""

    if tag_docs is not None:
        tag_name = tag_docs.name
        tag_id = putils.coalesce(tag_docs.exif_id, "")
        description = putils.coalesce(tag_docs.description, "")

    return (
        tag_docs_template
        .replace("<tag_name>", tag_name)
        .replace("<tag_id>", tag_id)
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
