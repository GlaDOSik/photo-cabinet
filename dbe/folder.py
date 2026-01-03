import uuid
from typing import Optional, List
from uuid import UUID

from sqlalchemy import ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base

ROOT_FOLDER_ID = UUID("1587573f-2748-4562-8ffe-4b96506302da")
LIMBO_FOLDER_ID = UUID("177f99c4-84c8-4005-9103-ebde67fed9e4")

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
    photos: Mapped[List["Photo"]] = relationship(back_populates="folder")
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
