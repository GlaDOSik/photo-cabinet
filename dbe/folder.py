import uuid
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import ForeignKey, and_, Enum as SAEnum, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base
from domain.folder_type import FolderType
from domain.ordering_type import OrderingType

ROOT_FOLDER_ID = UUID("1587573f-2748-4562-8ffe-4b96506302da")
LIMBO_FOLDER_ID = UUID("177f99c4-84c8-4005-9103-ebde67fed9e4")
VIRTUAL_FOLDER_ID = UUID("0914d89e-deb7-4107-9557-76d50236f0ab")

class Folder(Base):
    __tablename__ = "folder"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE")
    )
    parent: Mapped[Optional["Folder"]] = relationship(
        back_populates="folders",
        remote_side=[id]
    )

    name: Mapped[str]
    folder_type: Mapped[FolderType] = mapped_column(
        SAEnum(
            FolderType,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        )
    )
    photos: Mapped[List["Photo"]] = relationship(
        foreign_keys="[Photo.folder_id]",
        back_populates="folder"
    )
    v_photos: Mapped[List["Photo"]] = relationship(
        foreign_keys="[Photo.virtual_folder_id]",
        back_populates="virtual_folder"
    )
    folders: Mapped[List["Folder"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    def is_limbo(self):
        return self.parent is None and self.id == LIMBO_FOLDER_ID

def find_by_id(session: Session, id):
    return session.query(Folder).filter_by(id=id).first()

def find_root(session: Session):
    return session.query(Folder).filter_by(id=ROOT_FOLDER_ID).first()

def find_limbo(session: Session):
    return session.query(Folder).filter_by(id=LIMBO_FOLDER_ID).first()

def get_all_by_type(session: Session, folder_type: FolderType, offset: int = 0, limit: int = 1000):
    return session.query(Folder).filter_by(folder_type=folder_type).offset(offset).limit(limit).all()

def find_child_folders_by_parent(session: Session, parent_id: UUID, ordering: OrderingType, page: int, items_per_page: int) -> List[Folder]:
    return _child_folders_by_parent_query(session, parent_id, ordering).limit(items_per_page).offset(page * items_per_page).all()

def child_folders_by_parent_count(session: Session, parent_id: UUID, ordering: OrderingType):
    return _child_folders_by_parent_query(session, parent_id, ordering).count()

def _child_folders_by_parent_query(session: Session, parent_id: UUID, ordering: OrderingType):
    # Order folders - always alphabetical (folders don't have created date)
    if ordering == OrderingType.ALPHABETICAL_ASC:
        return session.query(Folder).filter_by(parent_id=parent_id).order_by(Folder.name)
    else:  # ALPHABETICAL_DESC
        return session.query(Folder).filter_by(parent_id=parent_id).order_by(desc(Folder.name))

def find_child_folder_ids_by_parent(session: Session, parent_id: UUID, limit: int) -> Tuple[List[UUID], bool]:
    """
    Returns tuple of (folder_ids, limit_reached).
    Queries exactly limit items and checks if total count exceeds limit.
    """
    query = session.query(Folder.id).filter_by(parent_id=parent_id).order_by(Folder.name)
    folder_ids = [row[0] for row in query.limit(limit).all()]
    total_count = session.query(Folder).filter_by(parent_id=parent_id).count()
    limit_reached = total_count > limit
    return (folder_ids, limit_reached)
