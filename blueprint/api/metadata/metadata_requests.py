from typing import Dict
from uuid import UUID

from marshmallow import Schema, fields, validate

from domain.metadata_index_type import MetadataIndexType


class GetPhotoMetadataRequest(Schema):
    photo_id = fields.Str(required=True, load_only=True)
    type = fields.Str(
        required=True,
        load_only=True,
        validate=validate.OneOf([e.value for e in MetadataIndexType])
    )

    @staticmethod
    def get_photo_id(request: Dict) -> UUID:
        return UUID(request.get("photo_id"))

    @staticmethod
    def get_type(request: Dict) -> MetadataIndexType:
        return MetadataIndexType(request.get("type"))
