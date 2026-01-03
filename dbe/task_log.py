import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, Session

from database import Base
from domain.task.task_log_severity import TaskLogSeverity


class TaskLog(Base):
    __tablename__ = "task_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("task.id"))

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    severity: Mapped[TaskLogSeverity] = mapped_column(
        SAEnum(
            TaskLogSeverity,
            native_enum=False,  # store as VARCHAR, not PG ENUM
            create_constraint=False,  # no CHECK constraint → no DB migration for new values
            validate_strings=True,  # Python-side validation
        ),
        default=TaskLogSeverity.INFO
    )
    message: Mapped[str]

def find_by_task_id(session: Session, task_id):
    return session.query(TaskLog).filter_by(task_id=task_id).all()