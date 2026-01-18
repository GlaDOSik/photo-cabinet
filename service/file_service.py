import uuid
from typing import Tuple, List, Optional, Set
from uuid import UUID

from sqlalchemy import select, literal, desc, asc, nullslast, update
from sqlalchemy.orm import Session, aliased

from dbe.folder import Folder
from dbe.photo import Photo
from domain.folder_content import FolderContent
from domain.folder_type import FolderType
from domain.ordering_type import OrderingType
from indexing.dbe.metadata_index import MetadataIndex


def get_breadcrumb(session: Session, folder_id: uuid.UUID) -> List[Folder]:
    # WITH RECURSIVE ancestors(id, parent_id, name, depth) AS (
    #   SELECT id, parent_id, name, 0 FROM folder WHERE id = :folder_id
    #   UNION ALL
    #   SELECT p.id, p.parent_id, p.name, a.depth + 1
    #   FROM folder p JOIN ancestors a ON p.id = a.parent_id
    # )
    # SELECT * FROM ancestors ORDER BY depth DESC;
    ancestors = (
        select(
            Folder.id, Folder.parent_id, Folder.name, literal(0).label("depth")
        )
        .where(Folder.id == folder_id)
        .cte(name="ancestors", recursive=True)
    )

    parent = aliased(Folder)
    ancestors = ancestors.union_all(
        select(parent.id, parent.parent_id, parent.name, ancestors.c.depth + 1)
        .join(parent, parent.id == ancestors.c.parent_id)
    )

    # Map CTE rows back to Folder instances ordered root → current
    return session.scalars(
        select(Folder)
        .join(ancestors, ancestors.c.id == Folder.id)
        .order_by(ancestors.c.depth.desc())
    ).all()

def get_folder_contents(session: Session, folder_id: UUID, ordering_type: Optional[OrderingType] = None) -> FolderContent:
    if ordering_type is None:
        ordering_type = OrderingType.ALPHABETICAL_ASC
    
    # Order folders - always alphabetical (folders don't have created date)
    if ordering_type == OrderingType.ALPHABETICAL_ASC or ordering_type == OrderingType.CREATED_DATE_ASC:
        folder_order = Folder.name
    else:  # ALPHABETICAL_DESC or CREATED_DATE_DESC
        folder_order = desc(Folder.name)
    
    child_folders = session.scalars(
        select(Folder).where(Folder.parent_id == folder_id).order_by(folder_order)
    ).all()
    
    # Order photos
    if ordering_type == OrderingType.ALPHABETICAL_ASC:
        photo_order = Photo.name
    elif ordering_type == OrderingType.ALPHABETICAL_DESC:
        photo_order = desc(Photo.name)
    elif ordering_type == OrderingType.CREATED_DATE_ASC:
        photo_order = nullslast(asc(MetadataIndex.photo_created))
    else:  # CREATED_DATE_DESC
        photo_order = nullslast(desc(MetadataIndex.photo_created))
    
    photos = session.scalars(
        select(Photo)
        .outerjoin(MetadataIndex, Photo.id == MetadataIndex.photo_id)
        .where(Photo.folder_id == folder_id)
        .order_by(photo_order)
    ).all()
    return FolderContent(child_folders, photos)


def _find_all_virtual_descendant_folders(session: Session, folder_id: UUID) -> Set[UUID]:
    """
    Recursively find all virtual descendant folders starting from the given folder_id.
    Returns a set of folder IDs including the root folder if it's virtual.
    """
    descendants = (
        select(
            Folder.id, Folder.parent_id, Folder.folder_type, literal(0).label("depth")
        )
        .where(Folder.id == folder_id)
        .cte(name="descendants", recursive=True)
    )
    
    child = aliased(Folder)
    descendants = descendants.union_all(
        select(child.id, child.parent_id, child.folder_type, descendants.c.depth + 1)
        .join(child, child.parent_id == descendants.c.id)
        .where(child.folder_type == FolderType.VIRTUAL)
    )
    
    folder_ids = session.scalars(
        select(descendants.c.id)
        .where(descendants.c.folder_type == FolderType.VIRTUAL)
    ).all()
    
    return set(folder_ids)


def remove_selection(session: Session, folder_ids: List[UUID], photo_ids: List[UUID]):
    """
    Remove selection: unset virtual_folder_id for photos and remove virtual folders recursively.
    
    - Sets virtual_folder_id to None for all photo_ids
    - For each folder_id that is VIRTUAL:
      - Recursively finds all child virtual folders
      - Unsets virtual_folder_id to None for all photos referencing these folders
      - Removes the virtual folders
    """
    # First, unset virtual_folder_id for all photo_ids
    if photo_ids:
        session.execute(
            update(Photo)
            .where(Photo.id.in_(photo_ids))
            .values(virtual_folder_id=None)
        )
    
    # Process each folder_id
    all_folder_ids_to_delete: Set[UUID] = set()
    
    for folder_id in folder_ids:
        folder = session.query(Folder).filter_by(id=folder_id).first()
        if folder is None:
            continue
        
        if folder.folder_type != FolderType.VIRTUAL:
            continue
        
        # Recursively find all virtual descendant folders
        descendant_ids = _find_all_virtual_descendant_folders(session, folder_id)
        all_folder_ids_to_delete.update(descendant_ids)
    
    # Unset virtual_folder_id for all photos referencing folders to be deleted
    if all_folder_ids_to_delete:
        session.execute(
            update(Photo)
            .where(Photo.virtual_folder_id.in_(all_folder_ids_to_delete))
            .values(virtual_folder_id=None)
        )
    
    # Delete all virtual folders
    if all_folder_ids_to_delete:
        # Delete in reverse depth order (children first) to avoid constraint issues
        # Using CASCADE delete, but we need to ensure order
        session.query(Folder).filter(Folder.id.in_(all_folder_ids_to_delete)).delete(synchronize_session=False)

