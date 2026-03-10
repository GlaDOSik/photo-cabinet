from database import Base, engine
from dbe.app_data import AppData  # noqa: F401
from dbe.docs.docs_et_group import DocsExifToolGroup  # noqa: F401
from dbe.docs.docs_et_tag import DocsExifToolTag  # noqa: F401
from dbe.docs.docs_et_value import DocsExifToolValue  # noqa: F401
from dbe.folder import Folder  # noqa: F401
from dbe.photo import Photo  # noqa: F401
from dbe.task import Task  # noqa: F401
from dbe.task_log import TaskLog  # noqa: F401
from dbe.wiki_page import WikiPage  # noqa: F401
from indexing.dbe.file_metadata_cache import FileMetadataCache  # noqa: F401
from indexing.dbe.metadata_index import MetadataIndex  # noqa: F401
from indexing.dbe.metadata_indexing_group import MetadataIndexingGroup  # noqa: F401
from indexing.dbe.metadata_indexing_tag import MetadataIndexingTag  # noqa: F401

if __name__ == "__main__":
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
