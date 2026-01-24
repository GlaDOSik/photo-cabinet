from flask import g, abort
from flask_smorest import Blueprint

from dbe.photo import find_by_id as find_photo_by_id
from blueprint.api.metadata.metadata_responses import PhotoMetadataIndex
from blueprint.api.metadata.metadata_requests import GetPhotoMetadataRequest
from domain.metadata_index_type import MetadataIndexType


metadata_api = Blueprint("metadata", __name__, url_prefix="/metadata")


@metadata_api.route("/photo", methods=["POST"])
@metadata_api.arguments(GetPhotoMetadataRequest, location="json")
@metadata_api.response(200, PhotoMetadataIndex)
@metadata_api.alt_response(404)
@metadata_api.alt_response(400)
def get_photo_metadata(request: dict):
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
    
    return PhotoMetadataIndex.to_resp(metadata_json)
