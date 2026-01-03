from database import Base, engine
from dbe import task_log, task, folder, photo, app_data
from indexing.dbe import metadata_index, metadata_indexing_group, metadata_indexing_tag
from exiftool.dbe import et_tag, et_group, et_value

if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)