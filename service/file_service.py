from typing import Tuple
from uuid import UUID

from sqlalchemy import select, literal
from sqlalchemy.orm import Session, aliased

from dbe.folder import Folder
from dbe.photo import Photo
from domain.folder_content import FolderContent


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

def get_folder_contents(session: Session, folder_id: UUID) -> FolderContent:
    child_folders = session.scalars(
        select(Folder).where(Folder.parent_id == folder_id).order_by(Folder.name)
    ).all()
    photos = session.scalars(
        select(Photo).where(Photo.folder_id == folder_id).order_by(Photo.filename)
    ).all()
    return FolderContent(child_folders, photos)