from domain.metadata.metadata_group_0 import MetadataGroup0
from domain.metadata.metadata_group_1 import MetadataGroup1
from domain.metadata.metadata_id import MetadataId
from domain.metadata.metadata_name import MetadataName

EXIF_DATE_TIME_ORIGINAL = MetadataId.of(MetadataGroup0.EXIF, None, MetadataName.DATE_TIME_ORIGINAL)
EXIF_OFFSET_TIME_ORIG = MetadataId.of(MetadataGroup0.EXIF, None, MetadataName.OFFSET_TIME_ORIG)
EXIF_CREATE_DATE = MetadataId.of(MetadataGroup0.EXIF, None, MetadataName.CREATE_DATE)
EXIF_OFFSET_TIME_DIGIT = MetadataId.of(MetadataGroup0.EXIF, None, MetadataName.OFFSET_TIME_DIGIT)

XMP_EXIF_DATE_TIME_ORIGINAL = MetadataId.of(MetadataGroup0.XMP, MetadataGroup1.XMP_EXIF, MetadataName.DATE_TIME_ORIGINAL)
XMP_PHOTOSHOP_DATE_CREATED = MetadataId.of(MetadataGroup0.XMP, MetadataGroup1.XMP_PS, MetadataName.DATE_CREATED)

IPTC_DATE_CREATED = MetadataId.of(MetadataGroup0.IPTC, None, MetadataName.DATE_CREATED)
IPTC_TIME_CREATED = MetadataId.of(MetadataGroup0.IPTC, None, MetadataName.TIME_CREATED)