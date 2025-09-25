import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    parent_tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tag.id"))

    text: Mapped[str]