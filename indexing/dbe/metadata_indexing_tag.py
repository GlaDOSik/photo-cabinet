import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base


class MetadataIndexingTag(Base):
    __tablename__ = "metadata_indexing_tag"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("metadata_indexing_group.id", ondelete="CASCADE")
    )
    group: Mapped["MetadataIndexingGroup"] = relationship(back_populates="tags")
    order: Mapped[int]
    
    g0: Mapped[Optional[str]]
    g1: Mapped[Optional[str]]
    tag_name: Mapped[Optional[str]]
    tag_path: Mapped[Optional[str]]


def find_all(session: Session):
    return session.query(MetadataIndexingTag).all()

