from enum import Enum


class GroupType(Enum):
    INDEXING_FILTER = "FILTER"
    CREATED_DATE_GROUP = "CREATED_DATE_GRP"
    PHOTO_SIZE_GROUP = "PHOTO_SIZE_GRP"