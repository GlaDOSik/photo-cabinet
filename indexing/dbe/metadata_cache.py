from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base


class MetadataCache(Base):
    __tablename__ = "photo_metadata_cache"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    metadata_index_id: Mapped[UUID] = mapped_column(
        ForeignKey("photo_metadata.id", ondelete="CASCADE")
    )

    full_json = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    task_id: Mapped[Optional[UUID]]


def find_by_metadata_index_id(session: Session, metadata_index_id: UUID) -> MetadataCache | None:
    return session.query(MetadataCache).filter_by(metadata_index_id=metadata_index_id).first()
