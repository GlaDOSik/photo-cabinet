from typing import Dict, List
from uuid import UUID

from marshmallow import Schema, fields, validate

from blueprint.transfer.pagination_to import PaginationRequest
from domain.cursor_direction import CursorDirection
from domain.ordering_type import OrderingType

class GetFolderFoldersRequest(Schema):
    folder_id = fields.Str(required=True, load_only=True)
    pagination = fields.Nested(PaginationRequest, many=False, required=True)
    ordering = fields.Str(
        required=True,
        load_only=True,
        validate=validate.OneOf([OrderingType.ALPHABETICAL_ASC.name, OrderingType.ALPHABETICAL_DESC.name])
    )

    @staticmethod
    def get_folder_id(request: Dict) -> UUID:
        return UUID(request.get("folder_id"))

    @staticmethod
    def get_ordering(request: Dict) -> OrderingType:
        return OrderingType[request.get("ordering")]

    @staticmethod
    def get_pagination(request: Dict) -> Dict:
        return request.get("pagination")


class GetFolderPhotosRequest(Schema):
    folder_id = fields.Str(required=True, load_only=True)
    pagination = fields.Nested(PaginationRequest, many=False, required=True, load_only=True)
    ordering = fields.Str(
        required=True,
        load_only=True,
        validate=validate.OneOf([e.name for e in OrderingType])
    )

    @staticmethod
    def get_folder_id(request: Dict) -> UUID:
        return UUID(request.get("folder_id"))

    @staticmethod
    def get_ordering(request: Dict) -> OrderingType:
        return OrderingType[request.get("ordering")]

    @staticmethod
    def get_pagination(request: Dict) -> Dict:
        return request.get("pagination")


class GetFolderIdsRequest(Schema):
    folder_id = fields.Str(required=True, load_only=True)

    @staticmethod
    def get_folder_id(request: Dict) -> UUID:
        return UUID(request.get("folder_id"))


class GetPhotoIdsRequest(Schema):
    folder_id = fields.Str(required=True, load_only=True)

    @staticmethod
    def get_folder_id(request: Dict) -> UUID:
        return UUID(request.get("folder_id"))


class CreateFolderRequest(Schema):
    parent_id = fields.Str(required=True, load_only=True)
    folder_name = fields.Str(required=True, load_only=True)

    @staticmethod
    def get_parent_id(request: Dict) -> UUID:
        return UUID(request.get("parent_id"))

    @staticmethod
    def get_folder_name(request: Dict) -> str:
        return request.get("folder_name")


class SelectionRequest(Schema):
    folder_ids = fields.List(fields.Str(), required=False, load_only=True)
    photo_ids = fields.List(fields.Str(), required=False, load_only=True)

    @staticmethod
    def get_folder_ids(request: Dict) -> List[UUID]:
        folder_ids = request.get("folder_ids", [])
        return [UUID(fid) for fid in folder_ids]

    @staticmethod
    def get_photo_ids(request: Dict) -> List[UUID]:
        photo_ids = request.get("photo_ids", [])
        return [UUID(pid) for pid in photo_ids]


class RemoveSelectionRequest(Schema):
    selection = fields.Nested(SelectionRequest, many=False, required=True, load_only=True)

    @staticmethod
    def get_selection(request: Dict) -> Dict:
        return request.get("selection")


class MoveSelectionToFolderRequest(Schema):
    selection = fields.Nested(SelectionRequest, many=False, required=True, load_only=True)
    target_folder_id = fields.Str(required=True, load_only=True)

    @staticmethod
    def get_selection(request: Dict) -> Dict:
        return request.get("selection")

    @staticmethod
    def get_target_folder_id(request: Dict) -> UUID:
        return UUID(request.get("target_folder_id"))


# class FolderContentCursor(Schema):
#     folder_id = fields.Str(required=True, load_only=True)
#     direction = fields.Str(
#         required=True,
#         load_only=True,
#         validate=validate.OneOf([e.name for e in CursorDirection])
#     )
#     ordering = fields.Str(
#         required=True,
#         load_only=True,
#         validate=validate.OneOf([e.name for e in OrderingType])
#     )
#     created_date = fields.DateTime(required=False, load_only=True) # first breaker for created date ordering
#     photo_name = fields.Str(required=False, load_only=True) # first breaker for ALPHABETICAL ordering
#     photo_id = fields.Str(required=False, load_only=True) # second tie-breaker
#     limit = fields.Int(required=True, load_only=True)
