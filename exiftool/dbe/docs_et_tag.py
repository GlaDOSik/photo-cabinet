from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from database import Base
from exiftool.dbe.docs_et_group import DocsExifToolGroup


class DocsExifToolTag(Base):
    __tablename__ = "docs_exif_tag"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("docs_exif_group.id")
    )

    exif_group: Mapped[DocsExifToolGroup] = relationship()
    exif_id: Mapped[str]
    ## Name of tag or struct - usually flattened name
    ## Example: LookParameters
    name: Mapped[str]
    type: Mapped[str]
    ## English description
    description: Mapped[str]
    writable: Mapped[bool]
    ## Tag is tag = can contain list of values (int, str,...)
    ## Tag is struct = can contain other tags (search by parent_struct)
    is_list: Mapped[bool] = mapped_column(default=False)

    ## If its nested struct or tag, this is the field name
    ## Example: Parameters
    field_name: Mapped[Optional[str]]
    ## If the tag or struct is child of some parent struct
    ## Example: id of struct Look
    parent_struct_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("docs_exif_tag.id")
    )
    user_created: Mapped[bool] = mapped_column(default=False)


def find_by_group(session: Session, group_id: UUID):
    return session.query(DocsExifToolTag).filter_by(group_id=group_id).filter_by(deleted=False).filter_by(user_created=False).all()

