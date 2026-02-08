from typing import Dict

from marshmallow import Schema, fields


class PhotoMetadataIndex(Schema):
    ui_view = fields.Dict(
        keys=fields.Str(),
        values=fields.Raw(),
        required=True,
        allow_none=True
    )

    @staticmethod
    def to_resp(ui_view: Dict) -> Dict:
        return {"ui_view": ui_view}