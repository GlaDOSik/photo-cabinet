from flask_smorest import Blueprint
from blueprint.api.config.config_responses import ConfigResponse

config_api = Blueprint("config", __name__, url_prefix="/config")


@config_api.route("", methods=["GET"])
@config_api.response(200, ConfigResponse)
def get_config():
    return ConfigResponse.to_resp()

