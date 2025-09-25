import uuid

from flask import g
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields, validate
from dbe.task import find_by_id as find_task_by_id, Task
from domain.task.implementation.update_collection_task import UpdateCollectionTask
from domain.task.task_status import TaskStatus
from domain.task.task_type import TaskType
from service.task_service import task_service

task_api = Blueprint("task", __name__, url_prefix="/task")

class TaskCreatedResponse(Schema):
    task_id = fields.Str(required=True, dump_only=True)
    type = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in TaskType]))

class TaskStatusResponse(Schema):
    task_id = fields.Str(required=True, dump_only=True)
    type = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in TaskType]))
    status = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in TaskStatus]))
    progress_max = fields.Int(required=False, dump_only=True)
    progress_current = fields.Int(required=False, dump_only=True)


@task_api.route("/update-collection", methods=["POST"])
@task_api.response(201, TaskCreatedResponse)
def update_collection_task():
    task = UpdateCollectionTask()
    task_type = task.get_type()
    task_id = task_service.create_task(task)
    return {"task_id": str(task_id), "type": task_type.name}

@task_api.route("/<task_id>", methods=["GET"])
@task_api.response(201, TaskStatusResponse)
@task_api.response(404)
@task_api.alt_response(400, description="Invalid UUID")
def get_task_status(task_id: str):
    try:
        task_id = uuid.UUID(task_id)
    except ValueError:
        abort(400, message="Invalid job_id format")

    transaction_session = getattr(g, "transaction_session", None)
    task: Task = find_task_by_id(transaction_session, task_id)
    if task is None:
        abort(404)

    return {"task_id": task_id, "type": task.type.name,
            "status": task.status.name, "progress_max": task.progress_max,
            "progress_current": task.progress_current}