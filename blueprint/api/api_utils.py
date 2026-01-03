from uuid import UUID
from dbe.task import Task, find_by_id as find_task_by_id
from flask import abort, g


def task_by_id(task_id):
    try:
        task_id = UUID(task_id)
    except ValueError:
        abort(400)

    transaction_session = getattr(g, "transaction_session", None)
    task: Task = find_task_by_id(transaction_session, task_id)
    if task is None:
        abort(404)

    return task