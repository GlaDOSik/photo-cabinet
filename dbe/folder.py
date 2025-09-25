import uuid
from typing import Optional, List
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Folder(Base):
    __tablename__ = "folder"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE")
    )
    parent: Mapped[Optional["Folder"]] = relationship(
        back_populates="children",
        remote_side=[id]
    )

    name: Mapped[str]
    photos: Mapped[List["Photo"]] = relationship(back_populates="folder")
    folders: Mapped[List["Folder"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan"
    )

