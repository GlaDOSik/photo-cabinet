from flask import Flask, g
import logging

from flask_smorest import Api
from blueprint.api import api_blueprint
from blueprint.api.settings.task_api import task_api
from blueprint.api.settings.settings_api import settings_api
from database import DBSession

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

    return app

def register_blueprints(app: Flask):
    api = Api(app)
    settings_api.register_blueprint(task_api)
    api_blueprint.register_blueprint(settings_api)
    api.register_blueprint(api_blueprint)
