from typing import Dict

from flask import g, abort
from flask_smorest import Blueprint

from dbe.photo import find_by_id as find_photo_by_id
from blueprint.api.metadata.metadata_responses import PhotoMetadataIndex, MetadataInfoResponse
from blueprint.api.metadata.metadata_requests import GetPhotoMetadataRequest, MetadataInfoRequest, MetadataIdRequest
from domain.metadata.metadata_sets import METADATA_UI_VIEW_ORDER
from domain.metadata_index_type import MetadataIndexType
from indexing import metadata_indexing_repository
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
@metadata_api.response(200, PhotoMetadataIndex)
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
    else:
        abort(400)

    # TODO Implement custom ordering
    return PhotoMetadataIndex.to_resp(metadata_indexing_repository.index_to_ui_view(metadata_json, METADATA_UI_VIEW_ORDER))
