from typing import Sequence, Tuple, List
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, tuple_
from sqlalchemy.orm import Mapped, mapped_column, Session

from database import Base


class ExifToolValue(Base):
    __tablename__ = "exif_value"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("exif_tag.id")
    )

    value: Mapped[str]

    user_created: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)


def find_by_tag_ids(session: Session, tag_ids: List[UUID]):
    return session.query(ExifToolValue).filter(ExifToolValue.tag_id.in_(tag_ids)).filter_by(deleted=False).filter_by(user_created=False).all()

