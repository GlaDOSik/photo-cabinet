from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, Session

from database import Base


class MetadataLiveCache(Base):
    __tablename__ = "photo_metadata_live_cache"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    photo_id: Mapped[UUID]  # weak reference to photo, no FK

    full_json = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


def find_by_photo_id(session: Session, photo_id: UUID) -> Optional[MetadataLiveCache]:
    return session.query(MetadataLiveCache).filter_by(photo_id=photo_id).first()


def delete_expired(session: Session, ttl_sec: int) -> int:
    cutoff = datetime.utcnow() - timedelta(seconds=ttl_sec)
    return session.query(MetadataLiveCache).filter(MetadataLiveCache.created_at < cutoff).delete()
