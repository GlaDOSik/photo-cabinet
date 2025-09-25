from enum import Enum


class TaskStatus(Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "PROGRESS"
    OK = "OK"
    ERROR = "ERROR"