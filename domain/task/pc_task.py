from abc import ABC, abstractmethod
from datetime import datetime

from database import DBSession
from dbe.task_log import TaskLog
from domain.task.task_log_severity import TaskLogSeverity
from domain.task.task_status import TaskStatus
from domain.task.task_type import TaskType
from dbe import task


class PhotoCabinetTask(ABC):
    def __init__(self):
        self.db_task_id = None
        self.task_transaction = None

    def log_message(self, message: str, severity=TaskLogSeverity.INFO):
        transaction = DBSession()
        task_log = TaskLog()
        task_log.task_id = self.db_task_id
        task_log.severity = severity
        task_log.message = message
        transaction.add(task_log)
        transaction.commit()
        transaction.close()

    def update_max_progress(self, max_progress: int):
        transaction = DBSession()
        db_task = task.find_by_id(transaction, self.db_task_id)
        db_task.progress_max = max_progress
        db_task.progress_current = 0
        transaction.add(db_task)
        transaction.commit()
        transaction.close()

    def increment_current_progress(self):
        transaction = DBSession()
        db_task = task.find_by_id(transaction, self.db_task_id)
        if db_task.progress_current is None:
            db_task.progress_current = 1
        else:
            db_task.progress_current = db_task.progress_current + 1
        transaction.add(db_task)
        transaction.commit()
        transaction.close()

    def set_in_progress(self):
        transaction = DBSession()
        db_task = task.find_by_id(transaction, self.db_task_id)
        db_task.status = TaskStatus.IN_PROGRESS
        db_task.start = datetime.now()

        transaction.add(db_task)
        transaction.commit()
        transaction.close()

    def set_ok(self):
        transaction = DBSession()
        db_task = task.find_by_id(transaction, self.db_task_id)
        db_task.status = TaskStatus.OK
        db_task.end = datetime.now()

        transaction.add(db_task)
        transaction.commit()
        transaction.close()
        self.task_transaction.commit()

    def set_error(self, msg: str):
        transaction = DBSession()
        db_task = task.find_by_id(transaction, self.db_task_id)
        db_task.status = TaskStatus.ERROR
        db_task.error_msg = msg
        db_task.end = datetime.now()

        transaction.add(db_task)
        transaction.commit()
        transaction.close()
        self.task_transaction.commit()

    @abstractmethod
    def get_type(self) -> TaskType:
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def _serialize_fields(self) -> dict:
        """Return subclass-specific fields."""

    @classmethod
    @abstractmethod
    def _deserialize_fields(cls, fields: dict):
        pass

    def to_payload(self):
        """Return (class_path, fields) so it's picklable."""
        cls_path = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        return cls_path, self._serialize_fields()

    @staticmethod
    def from_payload(payload: tuple) -> "OHTask":
        cls_path, fields = payload
        module_name, class_name = cls_path.rsplit(".", 1)
        mod = __import__(module_name, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls._deserialize_fields(fields)