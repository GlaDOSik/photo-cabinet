from uuid import UUID
from flask import g, abort
from flask_smorest import Blueprint

from blueprint.transfer.pagination_to import PaginationRequest, PaginationResponse
from dbe.app_data import get_app_data_val
from domain.app_data_field import AppDataField
from domain.folder_type import FolderType
from service import file_service
from dbe.folder import find_by_id as find_folder_by_id, find_child_folders_by_parent, child_folders_by_parent_count, find_child_folder_ids_by_parent, Folder
from dbe.photo import find_child_photos_by_folder, child_photos_by_folder_count, find_child_photo_ids_by_folder
from blueprint.api.folder.folder_responses import BreadcrumbsResponse, FolderResponse, ChildFoldersResponse, \
    ChildPhotosResponse, FolderIdsResponse, PhotoIdsResponse
from blueprint.api.folder.folder_requests import GetFolderFoldersRequest, GetFolderPhotosRequest, GetFolderIdsRequest, GetPhotoIdsRequest, CreateFolderRequest, RemoveSelectionRequest, SelectionRequest
from blueprint.api.photo.photo_responses import PhotoResponse

folder_api = Blueprint("folder", __name__, url_prefix="/folder")


@folder_api.route("/<folder_id>/breadcrumb", methods=["GET"])
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

@folder_api.route("/<folder_id>/info", methods=["GET"])
@folder_api.response(200, FolderResponse)
@folder_api.alt_response(404)
@folder_api.alt_response(400)
def get_folder_info(folder_id: str):
    try:
        folder_uuid = UUID(folder_id)
    except ValueError:
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    folder = find_folder_by_id(transaction_session, folder_uuid)
    if folder is None:
        abort(404)
    
    return FolderResponse.to_resp(folder)

@folder_api.route("/folders", methods=["POST"])
@folder_api.arguments(GetFolderFoldersRequest, location="json")
@folder_api.response(200, ChildFoldersResponse)
@folder_api.alt_response(400)
def get_child_folders(request: dict):
    try:
        folder_uuid = GetFolderFoldersRequest.get_folder_id(request)
    except (ValueError, KeyError):
        abort(400)
    
    try:
        ordering = GetFolderFoldersRequest.get_ordering(request)
    except (KeyError, ValueError):
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    folders_per_page: int = get_app_data_val(transaction_session, AppDataField.FOLDER_VIEW_FOLDERS_PAGINATION_COUNT)
    page: int = PaginationRequest.get_page(GetFolderFoldersRequest.get_pagination(request))

    folders = find_child_folders_by_parent(transaction_session, folder_uuid, ordering, page - 1, folders_per_page)
    folders_count = child_folders_by_parent_count(transaction_session, folder_uuid, ordering)

    has_next_page = page * folders_per_page < folders_count
    page_count = (folders_count + folders_per_page - 1) // folders_per_page

    pagination_resp = PaginationResponse.to_resp(page, folders_count, page_count, has_next_page)
    folders_resp = [FolderResponse.to_resp(f) for f in folders]
    return ChildFoldersResponse.to_resp(folders_resp, pagination_resp)

@folder_api.route("/photos", methods=["POST"])
@folder_api.arguments(GetFolderPhotosRequest, location="json")
@folder_api.response(200, ChildPhotosResponse)
@folder_api.alt_response(400)
def get_child_photos(request: dict):
    try:
        folder_uuid = GetFolderPhotosRequest.get_folder_id(request)
    except (ValueError, KeyError):
        abort(400)
    
    try:
        ordering = GetFolderPhotosRequest.get_ordering(request)
    except (KeyError, ValueError):
        abort(400)

    transaction_session = getattr(g, "transaction_session", None)
    photos_per_page: int = get_app_data_val(transaction_session, AppDataField.FOLDER_VIEW_PHOTOS_PAGINATION_COUNT)
    page: int = PaginationRequest.get_page(GetFolderPhotosRequest.get_pagination(request))

    photos = find_child_photos_by_folder(transaction_session, folder_uuid, ordering, page - 1, photos_per_page)
    photos_count = child_photos_by_folder_count(transaction_session, folder_uuid, ordering)

    has_next_page = page * photos_per_page < photos_count
    page_count = (photos_count + photos_per_page - 1) // photos_per_page

    pagination_resp = PaginationResponse.to_resp(page, photos_count, page_count, has_next_page)
    photos_resp = [PhotoResponse.to_resp(p) for p in photos]
    return ChildPhotosResponse.to_resp(photos_resp, pagination_resp)

@folder_api.route("/folder-ids", methods=["POST"])
@folder_api.arguments(GetFolderIdsRequest, location="json")
@folder_api.response(200, FolderIdsResponse)
@folder_api.alt_response(400)
def get_folder_ids(request: dict):
    try:
        folder_uuid = GetFolderIdsRequest.get_folder_id(request)
    except (ValueError, KeyError):
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    limit: int = get_app_data_val(transaction_session, AppDataField.FOLDER_CONTENT_IDS_LIMIT)
    
    folder_ids, limit_reached = find_child_folder_ids_by_parent(transaction_session, folder_uuid, limit)
    return FolderIdsResponse.to_resp(folder_ids, limit, limit_reached)

@folder_api.route("/photo-ids", methods=["POST"])
@folder_api.arguments(GetPhotoIdsRequest, location="json")
@folder_api.response(200, PhotoIdsResponse)
@folder_api.alt_response(400)
def get_photo_ids(request: dict):
    try:
        folder_uuid = GetPhotoIdsRequest.get_folder_id(request)
    except (ValueError, KeyError):
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    limit: int = get_app_data_val(transaction_session, AppDataField.FOLDER_CONTENT_IDS_LIMIT)
    
    photo_ids, limit_reached = find_child_photo_ids_by_folder(transaction_session, folder_uuid, limit)
    return PhotoIdsResponse.to_resp(photo_ids, limit, limit_reached)

@folder_api.route("/create", methods=["POST"])
@folder_api.arguments(CreateFolderRequest, location="json")
@folder_api.response(201, FolderResponse)
@folder_api.alt_response(400)
@folder_api.alt_response(404)
def create_folder(request: dict):
    try:
        parent_uuid = CreateFolderRequest.get_parent_id(request)
    except (ValueError, KeyError):
        abort(400)
    
    try:
        folder_name = CreateFolderRequest.get_folder_name(request)
    except KeyError:
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    parent_folder = find_folder_by_id(transaction_session, parent_uuid)
    
    if parent_folder is None:
        abort(404)
    
    if parent_folder.folder_type != FolderType.VIRTUAL:
        abort(400)
    
    new_folder = Folder()
    new_folder.name = folder_name
    new_folder.parent_id = parent_uuid
    new_folder.folder_type = FolderType.VIRTUAL
    transaction_session.add(new_folder)
    transaction_session.flush()
    
    return FolderResponse.to_resp(new_folder)

@folder_api.route("/remove-selection", methods=["POST"])
@folder_api.arguments(RemoveSelectionRequest, location="json")
@folder_api.response(204)
@folder_api.alt_response(400)
def remove_selection_endpoint(request: dict):
    try:
        selection = RemoveSelectionRequest.get_selection(request)
        folder_ids = SelectionRequest.get_folder_ids(selection)
        photo_ids = SelectionRequest.get_photo_ids(selection)
    except (ValueError, KeyError):
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    file_service.remove_selection(transaction_session, folder_ids, photo_ids)
    
    return "", 204