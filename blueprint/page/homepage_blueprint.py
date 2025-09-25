from flask_smorest import Blueprint

home_blueprint = Blueprint("home", __name__, url_prefix="/")

@home_blueprint.route("/", methods=["GET"])
def home_redirect():
    pass