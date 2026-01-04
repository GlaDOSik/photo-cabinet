from typing import Dict
from uuid import UUID
from flask import g, abort
from flask_smorest import Blueprint
from service import file_service
from dbe.folder import find_by_id as find_folder_by_id
from blueprint.api.folder.folder_responses import BreadcrumbsResponse, FolderResponse, FolderContentResponse
from blueprint.api.folder.folder_requests import FolderContentRequest
from blueprint.api.photo.photo_responses import PhotoResponse
from domain.ordering_type import OrderingType

folder_api = Blueprint("folder", __name__, url_prefix="/folder")


@folder_api.route("/breadcrumb/<folder_id>", methods=["GET"])
@folder_api.response(200, BreadcrumbsResponse)
@folder_api.alt_response(400)
def get_breadcrumbs(folder_id: str):
    try:
        folder_uuid = UUID(folder_id)
    except ValueError:
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    folders = file_service.get_breadcrumb(transaction_session, folder_uuid)
    folders_resp = [FolderResponse.to_resp(f) for f in folders]
    return BreadcrumbsResponse.to_resp(folders_resp)

@folder_api.route("/content", methods=["POST"])
@folder_api.arguments(FolderContentRequest)
@folder_api.response(200, FolderContentResponse)
@folder_api.alt_response(404)
@folder_api.alt_response(400)
def get_folder_content(request: Dict):
    folder_id_str = request.get("folder_id")
    if not folder_id_str:
        abort(400)
    
    try:
        folder_uuid = UUID(folder_id_str)
    except ValueError:
        abort(400)
    
    ordering_type = None
    ordering_type_str = request.get("ordering_type")
    if ordering_type_str:
        try:
            ordering_type = OrderingType[ordering_type_str]
        except (KeyError, ValueError):
            abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    folder = find_folder_by_id(transaction_session, folder_uuid)
    if folder is None:
        abort(404)
    
    folder_content = file_service.get_folder_contents(transaction_session, folder_uuid, ordering_type)
    
    current_folder_resp = FolderResponse.to_resp(folder)
    child_folders_resp = [FolderResponse.to_resp(f) for f in folder_content.folders]
    photos_resp = [PhotoResponse.to_resp(p) for p in folder_content.photos]
    
    return FolderContentResponse.to_resp(current_folder_resp, child_folders_resp, photos_resp)