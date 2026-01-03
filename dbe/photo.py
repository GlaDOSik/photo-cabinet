import uuid
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

import pc_configuration
from database import Base
from dbe.folder import Folder
from vial.config import app_config


class Photo(Base):
    __tablename__ = "photo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE")
    )
    folder: Mapped[Folder] = relationship(back_populates="photos")
    metadata_index: Mapped[Optional["MetadataIndex"]] = relationship(
        "MetadataIndex",
        uselist=False,
        lazy="select"
    )

    file_path: Mapped[str]
    file_hash: Mapped[str]

    name: Mapped[str]

    def get_photo_file_path(self):
        return app_config.get_configuration(pc_configuration.COLLECTION_PATH) + "/" + self.file_path

def get_all(session: Session):
    return session.query(Photo).all()

def find_by_path(session: Session, relative_path: str) -> Optional[Photo]:
    return session.query(Photo).filter_by(file_path=relative_path).first()

def find_by_hash(session: Session, file_hash: str):
    return session.query(Photo).filter_by(file_hash=file_hash).first()
