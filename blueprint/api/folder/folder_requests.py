from marshmallow import Schema, fields, validate

from domain.ordering_type import OrderingType


class FolderContentRequest(Schema):
    folder_id = fields.Str(required=True, load_only=True)
    ordering_type = fields.Str(
        required=False,
        load_only=True,
        validate=validate.OneOf([e.name for e in OrderingType])
    )

