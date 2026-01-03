from flask import g
from flask_smorest import Blueprint

from blueprint.api.task.task_responses import TaskStatusResponse
from service.task_service import task_service
from service.task.implementation.update_collection_task import RunScanAndIndexingTask
from dbe.task import find_by_id as find_task_by_id


indexing_api = Blueprint("indexing", __name__, url_prefix="/indexing")

@indexing_api.route("/scan-index", methods=["POST"])
@indexing_api.response(200, TaskStatusResponse)
def run_scan_indexing():
    transaction_session = getattr(g, "transaction_session", None)
    oh_task = RunScanAndIndexingTask()
    task_id = task_service.create_task(oh_task)
    db_task = find_task_by_id(transaction_session, task_id)
    return TaskStatusResponse.to_resp(db_task)