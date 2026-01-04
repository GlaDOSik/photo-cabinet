from typing import List

from marshmallow import Schema, fields, validate

from blueprint.api.photo.photo_responses import PhotoResponse
from dbe.folder import Folder
from domain.folder_type import FolderType

class FolderResponse(Schema):
    id = fields.Str(required=True, dump_only=True)
    parent_id = fields.Str(required=False, dump_only=True)
    name = fields.Str(required=True, dump_only=True)
    type = fields.Str(required=True, dump_only=True, validate=validate.OneOf([e.name for e in FolderType]))

    @staticmethod
    def to_resp(folder: Folder):
        resp_dict = {"id": str(folder.id), "name": folder.name, "type": folder.folder_type.name}
        if folder.parent_id is not None:
            resp_dict["parent_id"] = str(folder.parent_id)
        return resp_dict

class FolderContentResponse(Schema):
    current_folder = fields.Nested(FolderResponse, many=False, required=True)
    child_folders = fields.Nested(FolderResponse, many=True, required=False)
    photos = fields.Nested(PhotoResponse, many=True, required=False)

    @staticmethod
    def to_resp(current_folder: FolderResponse, child_folders: List[FolderResponse], photos: List[PhotoResponse]):
        return {"current_folder": current_folder, "child_folders": child_folders, "photos": photos}

class BreadcrumbsResponse(Schema):
    folders = fields.Nested(FolderResponse, many=True, required=True)

    @staticmethod
    def to_resp(folders: List[FolderResponse]):
        return {"folders": folders}