from enum import Enum, auto


class MetadataGroup1(Enum):
    XMP_EXIF = (auto(), "XMP-exif")
    XMP_PS = (auto(), "XMP-photoshop")

    def __new__(cls, value, metadata_name):
        obj = object.__new__(cls)
        obj._value_ = value  # unique, so no aliasing
        obj.metadata_name = metadata_name
        return obj