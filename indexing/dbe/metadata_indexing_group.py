import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from database import Base
from indexing.domain.filter_type import FilterType
from indexing.domain.group_type import GroupType


class MetadataIndexingGroup(Base):
    __tablename__ = "metadata_indexing_group"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    group_name: Mapped[str]
    file_path_match: Mapped[Optional[str]]
    group_type: Mapped[GroupType] = mapped_column(
        SAEnum(
            GroupType,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        )
    )

    filter_type: Mapped[Optional[FilterType]] = mapped_column(
        SAEnum(
            FilterType,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        )
    )
    
    tags: Mapped[List["MetadataIndexingTag"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="MetadataIndexingTag.order"
    )


def find_all(session: Session):
    return session.query(MetadataIndexingGroup).all()


def find_by_id(session: Session, id: UUID):
    return session.query(MetadataIndexingGroup).filter_by(id=id).first()


def find_matching_groups(session: Session, file_path: str, group_type: GroupType) -> List[MetadataIndexingGroup]:
    """
    Find all groups that match the given file path and group_type.
    Returns groups where file_path_match is None (global) or where
    file_path starts with file_path_match (prefix match).
    """
    from sqlalchemy import func, literal
    
    # Get global groups (file_path_match is None)
    global_groups = session.query(MetadataIndexingGroup).filter(
        MetadataIndexingGroup.file_path_match.is_(None),
        MetadataIndexingGroup.group_type == group_type
    ).all()
    
    # Get groups where file_path starts with file_path_match
    # Using SQL LIKE for prefix matching: file_path LIKE file_path_match || '%'
    prefix_groups = session.query(MetadataIndexingGroup).filter(
        MetadataIndexingGroup.file_path_match.isnot(None),
        literal(file_path).like(
            func.concat(MetadataIndexingGroup.file_path_match, '%')
        ),
        MetadataIndexingGroup.group_type == group_type
    ).all()
    
    return global_groups + prefix_groups

