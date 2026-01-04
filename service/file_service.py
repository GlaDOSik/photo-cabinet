import uuid
from typing import Tuple, List, Optional
from uuid import UUID

from sqlalchemy import select, literal, desc, asc, nullslast
from sqlalchemy.orm import Session, aliased

from dbe.folder import Folder
from dbe.photo import Photo
from domain.folder_content import FolderContent
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