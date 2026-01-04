from enum import Enum, auto


class MetadataName(Enum):
    DATE_TIME_ORIGINAL = (auto(), "DateTimeOriginal")
    CREATE_DATE = (auto(), "CreateDate")
    DATE_CREATED = (auto(), "DateCreated")
    OFFSET_TIME_ORIG = (auto(), "OffsetTimeOriginal")
    OFFSET_TIME_DIGIT = (auto(), "OffsetTimeDigitized")
    TIME_CREATED = (auto(), "TimeCreated")
    IMAGE_WIDTH = (auto(), "ImageWidth")
    IMAGE_HEIGHT = (auto(), "ImageHeight")
    EXIF_IMAGE_WIDTH = (auto(), "ExifImageWidth")
    EXIF_IMAGE_HEIGHT = (auto(), "ExifImageHeight")

    def __new__(cls, value, metadata_name):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.metadata_name = metadata_name
        return obj