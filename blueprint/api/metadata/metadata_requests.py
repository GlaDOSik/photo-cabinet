from typing import Dict
from uuid import UUID

from marshmallow import Schema, fields, validate, validates

from domain.metadata.metadata_id import MetadataId
from domain.metadata_index_type import MetadataIndexType

_TAG_UI_DELIMITER = " / "


class MetadataIdRequest(Schema):
    ui_view_tag_path = fields.List(fields.Raw())  # str or int per element
    tag_value = fields.Raw(required=False)

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
        g0 = tag_path[0]
        g1 = None if tag_path[1] == "-" else tag_path[1] # TODO - there could be only g0 defined in req, this will raise IndexError
        remaining = tag_path[2:]

        if not remaining:
            return MetadataId(g0, g1, None)

        tag_specifier = str(remaining[-1])
        path_nodes = remaining[:-1]

        if _TAG_UI_DELIMITER in tag_specifier:
            tag_name, tag_id = tag_specifier.split(_TAG_UI_DELIMITER, 1)
        else:
            tag_name, tag_id = tag_specifier, None

        path = "." + ".".join(str(n) for n in path_nodes) if path_nodes else None
        return MetadataId(g0, g1, tag_name, metadata_id=tag_id, path=path)

    @staticmethod
    def get_tag_value(request: Dict):
        return request.get("tag_value")


class MetadataInfoRequest(Schema):
    metadata_id = fields.Nested(MetadataIdRequest, many=False, required=True)

    @staticmethod
    def get_metadata_id(request: Dict) -> Dict:
        return request.get("metadata_id")


class GetPhotoChangesRequest(Schema):
    photo_id = fields.Str(required=True, load_only=True)

    @staticmethod
    def get_photo_id(request: Dict) -> UUID:
        return UUID(request.get("photo_id"))


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
