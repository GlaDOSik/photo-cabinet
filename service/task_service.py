import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from uuid import uuid4

from database import DBSession
from dbe.task import Task
from domain.task.pc_task import PhotoCabinetTask

# Create the pool lazily after workers fork (avoid preload_app=True issues)
_pool = None
def get_pool():
    global _pool
    if _pool is None:
        ctx = multiprocessing.get_context("forkserver")  # or "spawn" if forkserver unavailable
        _pool = ProcessPoolExecutor(max_workers=2, mp_context=ctx)
    return _pool

def _run_task_serialized(oh_task_dict):
    # This runs in a separate process
    oh = PhotoCabinetTask.from_payload(oh_task_dict)
    try:
        oh.task_transaction = DBSession()
        oh.set_in_progress()
        oh.execute()
        oh.set_ok()
    except Exception as ex:
        oh.set_error(str(ex))
        oh.task_transaction.rollback()
        raise
    finally:
        oh.task_transaction.close()

class TaskService:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers

    def create_task(self, oh_task: PhotoCabinetTask):
        db_task = Task()
        task_id = uuid4()
        db_task.id = task_id
        db_task.type = oh_task.get_type()
        oh_task.db_task_id = db_task.id

        transaction = DBSession()
        transaction.add(db_task)
        transaction.commit()
        transaction.close()

        get_pool().submit(_run_task_serialized, oh_task.to_payload())
        return task_id

task_service = TaskService(1)