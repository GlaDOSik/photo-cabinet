from typing import List

from marshmallow import Schema, fields, validate

from dbe.task import Task
from dbe.task_log import TaskLog as DbeTaskLog
from domain.task.task_log_severity import TaskLogSeverity
from domain.task.task_status import TaskStatus
from domain.task.task_type import TaskType

class TaskStatusResponse(Schema):
    id = fields.Str(required=True, dump_only=True)
    type = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in TaskType]))
    status = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in TaskStatus]))
    name = fields.Str(required=False, dump_only=True)
    progress_max = fields.Int(required=False, dump_only=True)
    progress_current = fields.Int(required=False, dump_only=True)
    error_msg = fields.Str(required=False, dump_only=True)
    start_time = fields.Str(required=False, dump_only=True)

    @staticmethod
    def to_resp(task: Task):
        resp_dict = {"id": str(task.id), "type": task.type.name, "status": task.status.name}
        if task.progress_max is not None:
            resp_dict["progress_max"] = task.progress_max
        if task.progress_current is not None:
            resp_dict["progress_current"] = task.progress_current
        if task.error_msg is not None:
            resp_dict["error_msg"] = task.error_msg
        if task.start is not None:
            resp_dict["start_time"] = task.start.strftime("%Y-%m-%d %H:%M:%S")
        if task.name is not None:
            resp_dict["name"] = task.name
        return resp_dict

class ListTasksResponse(Schema):
    tasks = fields.Nested(TaskStatusResponse, many=True, required=True)

    @staticmethod
    def to_resp(tasks: List[TaskStatusResponse]):
        return {"tasks": tasks}

class TaskLog(Schema):
    timestamp = fields.Str(required=True, dump_only=True)
    severity = fields.Str(required=True, dump_only=True, validate=validate.OneOf([s.name for s in TaskLogSeverity]))
    message = fields.Str(required=True, dump_only=True)

    @staticmethod
    def to_resp(task_log: DbeTaskLog):
        return {"timestamp": task_log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "severity": task_log.severity.name,
                "message": task_log.message}

class TaskLogs(Schema):
    task_id = fields.Str(required=True)
    logs = fields.Nested(TaskLog, many=True, required=True)

    @staticmethod
    def to_resp(task: Task, task_logs: List[TaskLog]):
        return {"task_id": str(task.id), "logs": task_logs}