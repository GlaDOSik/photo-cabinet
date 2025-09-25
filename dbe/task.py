import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, nullsfirst, desc
from sqlalchemy.orm import Mapped, mapped_column, Session
from sqlalchemy import Enum as SAEnum

from database import Base
from domain.task.task_status import TaskStatus
from domain.task.task_type import TaskType


class Task(Base):
    __tablename__ = "task"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    type: Mapped[TaskType] = mapped_column(
        SAEnum(
            TaskType,
            native_enum=False,  # store as VARCHAR, not PG ENUM
            create_constraint=False,  # no CHECK constraint → no DB migration for new values
            validate_strings=True,  # Python-side validation
        )
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(
            TaskStatus,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
        ), default=TaskStatus.WAITING
    )
    progress_max: Mapped[Optional[int]]
    progress_current: Mapped[Optional[int]]

    start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end: Mapped[Optional[datetime]] = mapped_column(DateTime)

    error_msg: Mapped[Optional[str]]


def find_by_id(session: Session, id):
    return session.query(Task).filter_by(id=id).first()

def get_all(session: Session):
    return session.query(Task).order_by(nullsfirst(desc(Task.start))).all()