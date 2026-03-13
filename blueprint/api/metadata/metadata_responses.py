from enum import Enum
from typing import Dict, Optional
from uuid import UUID

from marshmallow import Schema, fields, validate

from domain.metadata_index_type import MetadataIndexType


class PhotoMetadataStatus(Enum):
    READY = "READY"
    PENDING = "PENDING"


class PhotoMetadataIndex(Schema):
    ui_view = fields.Dict(
        keys=fields.Str(),
        values=fields.Raw(),
        required=True,
        allow_none=True
    )
    type = fields.Str(required=True, validate=validate.OneOf([e.value for e in MetadataIndexType]))

    @staticmethod
    def to_resp(ui_view: Dict, metadata_type: MetadataIndexType) -> Dict:
        return {"ui_view": ui_view, "type": metadata_type.value}


class PhotoMetadataResponse(Schema):
    status = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.value for e in PhotoMetadataStatus]))
    data = fields.Nested(PhotoMetadataIndex, allow_none=True)

    @staticmethod
    def to_resp(
        status: PhotoMetadataStatus,
        ui_view: Optional[Dict] = None,
        metadata_type: Optional[MetadataIndexType] = None,
    ) -> Dict:
        data = PhotoMetadataIndex.to_resp(ui_view, metadata_type) if ui_view is not None else None
        return {"status": status.value, "data": data}


class LiveMetadataPendingResponse(Schema):
    task_id = fields.Str(required=True)

    @staticmethod
    def to_resp(task_id: UUID) -> dict:
        return {"task_id": str(task_id)}


class MetadataInfoResponse(Schema):
    md_docs = fields.Str(required=True)

    @staticmethod
    def to_resp(md_docs: str) -> Dict:
        return {"md_docs": md_docs}


class MetadataIdSchema(Schema):
    g0 = fields.Str(required=True)
    g1 = fields.Str(allow_none=True)
    path = fields.Str(allow_none=True)
    tag_name = fields.Str(allow_none=True)
    tag_id = fields.Str(allow_none=True)


class IndexChangeSchema(Schema):
    type = fields.Str(required=True)
    metadata_id = fields.Nested(MetadataIdSchema, required=True)
    new_value = fields.Raw(allow_none=True)


class PhotoChangesResponse(Schema):
    changes = fields.List(fields.Nested(IndexChangeSchema), required=True)

    @staticmethod
    def to_resp(changes: list) -> Dict:
        return {"changes": changes}
