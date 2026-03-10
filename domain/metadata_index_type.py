from enum import Enum


class MetadataIndexType(Enum):
    EXIF = "EXIF" # metadata index in database before user changes
    EFFECTIVE = "EFFECTIVE" # metadata index in database with applied user changes
    LIVE = "LIVE" # current (but cashed) state of metadata in file
    EFFECTIVE_LIVE_PREVIEW = "EFFECTIVE_LIVE_PREV" # preview how would file look with user changes applied
