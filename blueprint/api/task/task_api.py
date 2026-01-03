from flask import g, Response
from flask_smorest import Blueprint

from blueprint.api.task.task_responses import TaskStatusResponse, ListTasksResponse, TaskLog, TaskLogs
from blueprint.api.api_utils import task_by_id
from dbe.task_log import find_by_task_id as find_task_logs_by_task_id
from dbe.task import Task, get_all as list_all_tasks

task_api = Blueprint("task", __name__, url_prefix="/task")

@task_api.route("/", methods=["GET"])
@task_api.response(200, ListTasksResponse)
def list_tasks():
    transaction_session = getattr(g, "transaction_session", None)
    tasks = list_all_tasks(transaction_session)
    tasks_resp = [TaskStatusResponse.to_resp(t) for t in tasks]
    return ListTasksResponse.to_resp(tasks_resp)

@task_api.route("/<task_id>", methods=["GET"])
@task_api.response(200, TaskStatusResponse)
@task_api.alt_response(404)
@task_api.alt_response(400)
def get_task_status(task_id: str):
    task: Task = task_by_id(task_id)
    return TaskStatusResponse.to_resp(task)

@task_api.route("/<task_id>", methods=["DELETE"])
@task_api.response(200)
@task_api.alt_response(404)
@task_api.alt_response(400)
def delete_task(task_id: str):
    transaction_session = getattr(g, "transaction_session", None)
    task: Task = task_by_id(task_id)

    task_logs = find_task_logs_by_task_id(transaction_session, task.id)
    for task_log in task_logs:
        transaction_session.delete(task_log)
    transaction_session.flush()
    transaction_session.delete(task)

    return Response(status=200)

@task_api.route("/log/<task_id>", methods=["GET"])
@task_api.response(200, TaskLogs)
@task_api.alt_response(404)
@task_api.alt_response(400)
def get_logs(task_id: str):
    transaction_session = getattr(g, "transaction_session", None)
    task: Task = task_by_id(task_id)
    task_logs = find_task_logs_by_task_id(transaction_session, task.id)

    logs_resp = [TaskLog.to_resp(l) for l in task_logs]
    return TaskLogs.to_resp(task, logs_resp)