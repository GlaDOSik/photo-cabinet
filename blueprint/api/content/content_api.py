from uuid import UUID
from flask import g, abort, send_file
from flask_smorest import Blueprint
from dbe.photo import find_by_id as find_photo_by_id

content_api = Blueprint("content", __name__, url_prefix="/content")


@content_api.route("/image/<photo_id>", methods=["GET"])
@content_api.response(200)
@content_api.alt_response(404)
@content_api.alt_response(400)
def get_image(photo_id: str):
    try:
        photo_uuid = UUID(photo_id)
    except ValueError:
        abort(400)
    
    transaction_session = getattr(g, "transaction_session", None)
    photo = find_photo_by_id(transaction_session, photo_uuid)
    if photo is None:
        abort(404)
    
    file_path = photo.get_photo_file_path()
    return send_file(file_path)