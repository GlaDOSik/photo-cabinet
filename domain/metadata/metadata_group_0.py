from enum import Enum, auto


class MetadataGroup0(Enum):
    FILE = (auto(), "File")
    EXIF = (auto(), "EXIF")
    XMP = (auto(), "XMP")
    IPTC = (auto(), "IPTC")

    def __new__(cls, value, metadata_name):
        obj = object.__new__(cls)
        obj._value_ = value  # unique, so no aliasing
        obj.metadata_name = metadata_name
        return obj