from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from indexing.dbe.metadata_cache import MetadataCache

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base


class MetadataIndex(Base):
    __tablename__ = "photo_metadata"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("photo.id", ondelete="CASCADE")
    )

    exif_json = mapped_column(JSONB, nullable=False)
    user_json = mapped_column(JSONB, nullable=True)
    effective_json = mapped_column(JSONB, nullable=True)

    photo_created: Mapped[Optional[datetime]]
    photo_created_origin: Mapped[Optional[str]] # MetadataId key

    width: Mapped[Optional[int]]
    height: Mapped[Optional[int]]
    size_origin: Mapped[Optional[str]]

    use_thumbnail: Mapped[bool] = mapped_column(default=False)
    preview_color_hex: Mapped[Optional[str]]

    cache: Mapped[Optional["MetadataCache"]] = relationship(lazy="select")

def find_by_photo_id(session: Session, photo_id: UUID):
    return session.query(MetadataIndex).filter_by(photo_id=photo_id).first()


