from typing import Dict

from flask import g, abort
from flask_smorest import Blueprint

from dbe.app_data import get_app_data_val
from dbe.photo import find_by_id as find_photo_by_id
from blueprint.api.metadata.metadata_responses import PhotoMetadataResponse, PhotoMetadataStatus, MetadataInfoResponse, PhotoChangesResponse
from blueprint.api.metadata.metadata_requests import GetPhotoMetadataRequest, MetadataInfoRequest, MetadataIdRequest, GetPhotoChangesRequest
from domain.app_data_field import AppDataField
from domain.metadata.metadata_sets import METADATA_UI_VIEW_ORDER
from domain.metadata_index_type import MetadataIndexType
from indexing import metadata_indexing_service
from indexing.customize.index_change import IndexChange
from indexing.metadata_indexing_facade import get_or_submit_live_cache
from service import metadata_docs_service


metadata_api = Blueprint("metadata", __name__, url_prefix="/index")


@metadata_api.route("/docs", methods=["POST"])
@metadata_api.arguments(MetadataInfoRequest, location="json")
@metadata_api.response(200, MetadataInfoResponse)
def get_metadata_info(request: Dict):
    metadata_id_request = MetadataInfoRequest.get_metadata_id(request)
    metadata_id = MetadataIdRequest.get_metadata_id(metadata_id_request)
    tag_value = MetadataIdRequest.get_tag_value(request)
    transaction_session = getattr(g, "transaction_session", None)
    md_docs = metadata_docs_service.search_docs(transaction_session, metadata_id, tag_value)
    return MetadataInfoResponse.to_resp(md_docs or "")

@metadata_api.route("/photo", methods=["POST"])
@metadata_api.arguments(GetPhotoMetadataRequest, location="json")
@metadata_api.response(200, PhotoMetadataResponse)
@metadata_api.alt_response(404)
@metadata_api.alt_response(400)
def get_photo_metadata(request: Dict):
    try:
        photo_uuid = GetPhotoMetadataRequest.get_photo_id(request)
        metadata_type = GetPhotoMetadataRequest.get_type(request)
    except (ValueError, KeyError):
        abort(400)

    transaction_session = getattr(g, "transaction_session", None)
    photo = find_photo_by_id(transaction_session, photo_uuid)
    if photo is None:
        abort(404)

    if photo.metadata_index is None:
        abort(404)

    if metadata_type == MetadataIndexType.EXIF:
        metadata_json = photo.metadata_index.exif_json
    elif metadata_type == MetadataIndexType.EFFECTIVE:
        metadata_json = photo.metadata_index.effective_json
        if metadata_json is None:
            metadata_json = photo.metadata_index.exif_json
    elif metadata_type == MetadataIndexType.LIVE:
        ttl_sec = get_app_data_val(transaction_session, AppDataField.FILE_METADATA_CACHE_VALIDITY_SEC)
        full_json, task_id = get_or_submit_live_cache(transaction_session, photo, ttl_sec)
        if task_id is not None:
            return PhotoMetadataResponse.to_resp(PhotoMetadataStatus.PENDING)
        return PhotoMetadataResponse.to_resp(
            PhotoMetadataStatus.READY,
            metadata_indexing_service.index_to_ui_view(full_json, METADATA_UI_VIEW_ORDER),
            metadata_type,
        )
    else:
        abort(400)

    # TODO Implement custom ordering using tag groups (they are already used for getting photo creation date and photo size)
    # TODO Review ordering. Does it work only for g0 and g1? Or you can order also tags?
    return PhotoMetadataResponse.to_resp(
        PhotoMetadataStatus.READY,
        metadata_indexing_service.index_to_ui_view(metadata_json, METADATA_UI_VIEW_ORDER),
        metadata_type,
    )


@metadata_api.route("/photo/changes", methods=["POST"])
@metadata_api.arguments(GetPhotoChangesRequest, location="json")
@metadata_api.response(200, PhotoChangesResponse)
@metadata_api.alt_response(400)
@metadata_api.alt_response(404)
def get_photo_changes(request: Dict):
    try:
        photo_uuid = GetPhotoChangesRequest.get_photo_id(request)
    except (ValueError, KeyError):
        abort(400)

    transaction_session = getattr(g, "transaction_session", None)
    photo = find_photo_by_id(transaction_session, photo_uuid)
    if photo is None:
        abort(404)

    if photo.metadata_index is None or photo.metadata_index.user_json is None:
        return PhotoChangesResponse.to_resp([])

    changes = [IndexChange.from_dict(c).to_dict() for c in photo.metadata_index.user_json]
    return PhotoChangesResponse.to_resp(changes)
