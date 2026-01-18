from typing import List
from marshmallow import Schema, fields
from dbe.photo import Photo

class PhotoResponse(Schema):
    id = fields.Str(required=True, dump_only=True)
    name = fields.Str(required=True, dump_only=True)
    created_date = fields.DateTime(required=False, dump_only=True)
    width = fields.Int(required=True, dump_only=True)
    height = fields.Int(required=True, dump_only=True)
    use_thumbnail = fields.Bool(required=True, dump_only=True)
    preview_color_hex = fields.Str(required=True, dump_only=True)

    @staticmethod
    def to_resp(photo: Photo):
        photo_base = {"id": str(photo.id), "name": photo.name}
        if photo.metadata_index is not None:
            photo_base["width"] = photo.metadata_index.width
            photo_base["height"] = photo.metadata_index.height
            photo_base["use_thumbnail"] = photo.metadata_index.use_thumbnail
            photo_base["preview_color_hex"] = photo.metadata_index.preview_color_hex
            if photo.metadata_index.photo_created is not None:
                photo_base["created_date"] = photo.metadata_index.photo_created
        return photo_base
