from flask import Flask, g
import logging

from flask_cors import CORS
from flask_smorest import Api
from blueprint.api import api_blueprint
from blueprint.api.content.content_api import content_api
from blueprint.api.config.config_api import config_api
from blueprint.api.folder.folder_api import folder_api
from blueprint.api.metadata.metadata_api import metadata_api
from blueprint.api.settings.indexing.indexing_api import indexing_api
from blueprint.api.task.task_api import task_api
from blueprint.api.settings.settings_api import settings_api
from database import DBSession

from dbe import task_log, task, folder, photo, app_data
from indexing.dbe import metadata_index, metadata_indexing_group, metadata_indexing_tag
from exiftool.dbe import et_tag, et_group, et_value

logger = logging.getLogger()


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["API_TITLE"] = "Gallery API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"
    register_blueprints(app)

    @app.before_request
    def before_request():
        g.transaction_session = DBSession()

    @app.after_request
    def shutdown_session(response):
        transaction_session = getattr(g, "transaction_session", None)

        if transaction_session is None:
            return response

        try:
            transaction_session.commit()
        except BaseException as ex:
            transaction_session.rollback()
            logger.error("Commit failed with error: " + str(ex))
        finally:
            transaction_session.close()

        return response

    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173"]}},
        supports_credentials=True,  # if you use cookies/auth
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=3600,
    )
    return app

def register_blueprints(app: Flask):
    api = Api(app)
    settings_api.register_blueprint(task_api)
    settings_api.register_blueprint(indexing_api)
    api_blueprint.register_blueprint(settings_api)
    api_blueprint.register_blueprint(folder_api)
    api_blueprint.register_blueprint(content_api)
    api_blueprint.register_blueprint(config_api)
    api_blueprint.register_blueprint(metadata_api)

    api.register_blueprint(api_blueprint)
