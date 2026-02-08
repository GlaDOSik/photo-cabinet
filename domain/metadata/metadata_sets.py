from domain.metadata import metadata_defined
from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_id import MetadataId

CREATE_DATE_SET = [metadata_defined.EXIF_DATE_TIME_ORIGINAL, # Date, time
                   metadata_defined.EXIF_OFFSET_TIME_ORIG, # TZ for ^
                   metadata_defined.EXIF_CREATE_DATE, # Date, time
                   metadata_defined.EXIF_OFFSET_TIME_DIGIT, # TZ for ^
                   metadata_defined.XMP_EXIF_DATE_TIME_ORIGINAL,
                   metadata_defined.XMP_PHOTOSHOP_DATE_CREATED, # Date, time, TZ
                   metadata_defined.IPTC_DATE_CREATED, # Date
                   metadata_defined.IPTC_TIME_CREATED] # Time and TZ for ^

PHOTO_SIZE_SET = [metadata_defined.FILE_WIDTH,
              metadata_defined.FILE_HEIGHT,
              metadata_defined.EXIF_WIDTH,
              metadata_defined.EXIF_HEIGHT]

METADATA_UI_VIEW_ORDER = [metadata_defined.G0_FILE,
                          metadata_defined.G0_EXIF]
