from typing import List
from uuid import UUID

from marshmallow import Schema, fields, validate

from blueprint.api.photo.photo_responses import PhotoResponse
from blueprint.transfer.pagination_to import PaginationResponse
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


class ChildFoldersResponse(Schema):
    folders = fields.Nested(FolderResponse, many=True, required=True)
    pagination = fields.Nested(PaginationResponse, many=False, required=True)

    @staticmethod
    def to_resp(folders: List[FolderResponse], pagination: PaginationResponse):
        return {"folders": folders, "pagination": pagination}


class ChildPhotosResponse(Schema):
    photos = fields.Nested(PhotoResponse, many=True, required=True)
    pagination = fields.Nested(PaginationResponse, many=False, required=True)

    @staticmethod
    def to_resp(photos: List[PhotoResponse], pagination: PaginationResponse):
        return {"photos": photos, "pagination": pagination}


class FolderIdsResponse(Schema):
    folder_ids = fields.List(fields.Str(), required=True)
    limit = fields.Int(required=True)
    limit_reached = fields.Bool(required=True)

    @staticmethod
    def to_resp(folder_ids: List[UUID], limit: int, limit_reached: bool):
        return {
            "folder_ids": [str(fid) for fid in folder_ids],
            "limit": limit,
            "limit_reached": limit_reached
        }


class PhotoIdsResponse(Schema):
    photo_ids = fields.List(fields.Str(), required=True)
    limit = fields.Int(required=True)
    limit_reached = fields.Bool(required=True)

    @staticmethod
    def to_resp(photo_ids: List[UUID], limit: int, limit_reached: bool):
        return {
            "photo_ids": [str(pid) for pid in photo_ids],
            "limit": limit,
            "limit_reached": limit_reached
        }


class BreadcrumbsResponse(Schema):
    folders = fields.Nested(FolderResponse, many=True, required=True)

    @staticmethod
    def to_resp(folders: List[FolderResponse]):
        return {"folders": folders}