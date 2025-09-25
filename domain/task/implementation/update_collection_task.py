from pathlib import Path
from time import sleep

from domain.task.pc_task import PhotoCabinetTask
from domain.task.task_type import TaskType
from vial.config import app_config
import pc_configuration


class UpdateCollectionTask(PhotoCabinetTask):

    def get_type(self) -> TaskType:
        return TaskType.UPDATE_COLLECTION

    def _serialize_fields(self):
        return {"db_task_id": self.db_task_id}

    @classmethod
    def _deserialize_fields(cls, fields: dict):
        task = cls()
        task.db_task_id = fields["db_task_id"]
        return task

    def execute(self):
        root = Path(app_config.get_configuration(pc_configuration.COLLECTION_PATH))

        # first pass: count
        # file_count = sum(1 for _ in root.rglob("*") if _.is_file())
        self.update_max_progress(50)
        for i in range(50):
            sleep(1.0)
            self.increment_current_progress()