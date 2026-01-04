from marshmallow import Schema, fields

from dbe.photo import Photo


class PhotoResponse(Schema):
    id = fields.Str(required=True, dump_only=True)
    name = fields.Str(required=True, dump_only=True)

    @staticmethod
    def to_resp(photo: Photo):
        return {"id": str(photo.id), "name": photo.name}