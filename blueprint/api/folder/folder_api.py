from flask_smorest import Blueprint


folder_api = Blueprint("folder", __name__, url_prefix="/folder")

@folder_api.route("/scan-index", methods=["POST"])
def get_folder_content():
    pass