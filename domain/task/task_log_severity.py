from enum import Enum, auto


class TaskLogSeverity(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()