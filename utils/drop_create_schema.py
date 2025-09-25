from database import Base, engine
from dbe.task import Task
from dbe.task_log import TaskLog
from dbe.photo import Photo
from dbe.folder import Folder

if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)