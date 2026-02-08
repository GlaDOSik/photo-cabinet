from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from sqlalchemy import Enum as SAEnum


class WikiPage(Base):
    __tablename__ = "wiki_page"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    updated: Mapped[datetime] = mapped_column(DateTime)

    md_content: Mapped[str]