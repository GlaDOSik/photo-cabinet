import uuid
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import ForeignKey, desc, asc, nullslast
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

import pc_configuration
from database import Base
from dbe.folder import Folder
from vial.config import app_config
from domain.ordering_type import OrderingType
from indexing.dbe.metadata_index import MetadataIndex


class Photo(Base):
    __tablename__ = "photo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folder.id")
    )
    virtual_folder_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("folder.id")
    )
    folder: Mapped[Folder] = relationship(
        foreign_keys=[folder_id],
        back_populates="photos"
    )
    virtual_folder: Mapped[Folder] = relationship(
        foreign_keys=[virtual_folder_id],
        back_populates="v_photos"
    )
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

    def get_photo_thumbnail_path(self):
        return app_config.get_configuration(pc_configuration.GENERATED_PATH) + "/" + str(self.id) + ".jpg"

def get_all(session: Session):
    return session.query(Photo).all()

def get_all_paginated(session: Session, offset: int = 0, limit: int = 1000):
    return session.query(Photo).offset(offset).limit(limit).all()

def find_by_id(session: Session, id):
    return session.query(Photo).filter_by(id=id).first()

def find_by_path(session: Session, relative_path: str) -> Optional[Photo]:
    return session.query(Photo).filter_by(file_path=relative_path).first()

def find_by_hash(session: Session, file_hash: str):
    return session.query(Photo).filter_by(file_hash=file_hash).first()

def find_child_photos_by_folder(session: Session, folder_id: UUID, ordering: OrderingType, page: int, items_per_page: int):
    return _child_photos_by_folder_query(session, folder_id, ordering).limit(items_per_page).offset(page * items_per_page).all()

def child_photos_by_folder_count(session: Session, folder_id: UUID, ordering: OrderingType):
    return _child_photos_by_folder_query(session, folder_id, ordering).count()

def _child_photos_by_folder_query(session: Session, folder_id: UUID, ordering: OrderingType):
    # Order folders - always alphabetical (folders don't have created date)
    if ordering == OrderingType.ALPHABETICAL_ASC:
        return session.query(Photo).filter_by(folder_id=folder_id).order_by(Photo.name)
    elif ordering == OrderingType.ALPHABETICAL_DESC:  # ALPHABETICAL_DESC
        return session.query(Photo).filter_by(folder_id=folder_id).order_by(desc(Photo.name))
    elif ordering == OrderingType.CREATED_DATE_ASC:
        return session.query(Photo).outerjoin(MetadataIndex, Photo.id == MetadataIndex.photo_id).filter(Photo.folder_id == folder_id).order_by(nullslast(asc(MetadataIndex.photo_created)), Photo.name)
    elif ordering == OrderingType.CREATED_DATE_DESC:
        return session.query(Photo).outerjoin(MetadataIndex, Photo.id == MetadataIndex.photo_id).filter(Photo.folder_id == folder_id).order_by(nullslast(desc(MetadataIndex.photo_created)), Photo.name)

def find_child_photo_ids_by_folder(session: Session, folder_id: UUID, limit: int) -> Tuple[List[UUID], bool]:
    """
    Returns tuple of (photo_ids, limit_reached).
    Queries exactly limit items and checks if total count exceeds limit.
    Orders by name (alphabetical ascending) for consistency.
    """
    query = session.query(Photo.id).filter_by(folder_id=folder_id).order_by(Photo.name)
    photo_ids = [row[0] for row in query.limit(limit).all()]
    total_count = session.query(Photo).filter_by(folder_id=folder_id).count()
    limit_reached = total_count > limit
    return (photo_ids, limit_reached)
