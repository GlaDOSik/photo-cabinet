from typing import List

from dbe.folder import Folder
from dbe.photo import Photo


class FolderContent:
    def __init__(self, folders: List[Folder], photos: List[Photo]):
        self.folders: List[Folder] = folders
        self.photos: List[Photo] = photos