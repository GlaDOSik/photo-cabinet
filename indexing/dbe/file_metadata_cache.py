from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, desc
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, Session

from database import Base


class FileMetadataCache(Base):
    __tablename__ = "file_metadata_cache"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("photo.id", ondelete="CASCADE")
    )

    created: Mapped[datetime]
    valid_to: Mapped[datetime] = mapped_column(default=datetime.now)

    metadata_json = mapped_column(JSONB, nullable=False)


def find_latest(session: Session, photo_id: UUID) -> Optional[FileMetadataCache]:
    return session.query(FileMetadataCache).filter_by(photo_id=photo_id).order_by(desc(FileMetadataCache.created)).first()

def find_expired(session: Session):
    return session.query(FileMetadataCache) # TODO