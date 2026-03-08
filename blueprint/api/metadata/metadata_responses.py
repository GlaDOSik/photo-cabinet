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


class MetadataInfoResponse(Schema):
    md_docs = fields.Str(required=True)

    @staticmethod
    def to_resp(md_docs: str) -> Dict:
        return {"md_docs": md_docs}