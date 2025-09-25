import uuid
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

import pc_configuration
from database import Base
from dbe.association_tables.photo_x_tag import photo_x_tag_table
from dbe.folder import Folder
from dbe.tag import Tag
from vial.config import app_config


class Photo(Base):
    __tablename__ = "photo"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    folder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("folder.id", ondelete="CASCADE")
    )
    folder: Mapped[Folder] = relationship(back_populates="photos")

    file_path: Mapped[str]

    name: Mapped[str]
    created: Mapped[datetime]
    tags: Mapped[List[Tag]] = relationship(secondary=photo_x_tag_table, passive_deletes=True)

    def get_photo_file_path(self):
        return app_config.get_configuration(pc_configuration.COLLECTION_PATH) + "/" + self.file_path
