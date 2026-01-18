from marshmallow import Schema, fields

from dbe.folder import ROOT_FOLDER_ID, VIRTUAL_FOLDER_ID, LIMBO_FOLDER_ID


class ConfigResponse(Schema):
    root_folder_id = fields.Str(required=True, dump_only=True)
    limbo_folder_id = fields.Str(required=True, dump_only=True)
    virtual_folder_id = fields.Str(required=True, dump_only=True)

    @staticmethod
    def to_resp():
        return {"root_folder_id": str(ROOT_FOLDER_ID),
                "limbo_folder_id": str(LIMBO_FOLDER_ID),
                "virtual_folder_id": str(VIRTUAL_FOLDER_ID)}

