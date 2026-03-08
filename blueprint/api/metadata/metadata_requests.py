from typing import Dict, List
from uuid import UUID

from marshmallow import Schema, fields, validate, validates

from domain.metadata.metadata_id import MetadataId, PathStruct, PathArray
from domain.metadata_index_type import MetadataIndexType


class MetadataIdRequest(Schema):
    ui_view_tag_path = fields.List(fields.Raw())  # str or int per element, only path
    tag_name = fields.Str(required=False)
    tag_value = fields.Str(required=False)

    @validates("ui_view_tag_path")
    def validate_ui_view_tag_path(self, value, data_key):
        for item in value:
            if not isinstance(item, (str, int)):
                raise validate.ValidationError(
                    "Each element must be string or int"
                )

    @staticmethod
    def get_metadata_id(request: Dict) -> MetadataId:
        tag_path = request.get("ui_view_tag_path")
        g0 = None
        g1 = None
        path: List[PathStruct | PathArray] = []
        for i, tag_path_part in enumerate(tag_path):
            if i == 0:
                g0 = tag_path_part
            elif i == 1:
                g1 = None if tag_path_part == "-" else tag_path_part
            else:
                if isinstance(tag_path_part, int):
                    array_name = path[-1].struct_name
                    path.pop()
                    path.append(PathArray(array_name, tag_path_part))
                else:
                    path.append(PathStruct(tag_path_part))
        return MetadataId(g0, g1, request.get("tag_name"), path)

    @staticmethod
    def get_tag_value(request: Dict):
        return request.get("tag_value")


class MetadataInfoRequest(Schema):
    metadata_id = fields.Nested(MetadataIdRequest, many=False, required=True)

    @staticmethod
    def get_metadata_id(request: Dict) -> Dict:
        return request.get("metadata_id")


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
