from base64 import b64encode
from typing import Optional, Dict

from flask import Blueprint, request, Response

from vial.gui.component.gui_component import GuiComponent
from vial.webcallback.web_callback import WebCallback, WebCallbackResponse
from vial.webcallback.web_callback_registry import callback_registry
from vial.webcallback.web_component_data import WebComponentData
from vial.webcallback.web_data_registry import web_data_registry
import logging

web_callback_blueprint = Blueprint("vial", __name__, url_prefix="/vial")

log = logging.getLogger(__name__)


def _encode_base64_str(str_to_encode: str):
    return b64encode(str_to_encode.encode("utf-8")).decode("utf-8")


@web_callback_blueprint.route("/callback", methods=["POST"])
def callback():
    web_callback: Optional[WebCallback] = get_web_callback()

    if web_callback is None:
        log.error(f"Requested WebCallback {request.json.get("callback-name")} NOT found!")
        return Response("Bla", 500)

    web_component_data_json: {id, Dict} = request.json.get("web-component-data")
    for key, data in web_component_data_json.items():
        id_component_data_name = key.split(" - ")

        web_component_data: Optional[WebComponentData] = None
        web_component_data_found = False
        for cls in web_data_registry:
            if cls.__name__ == id_component_data_name[1]:
                web_component_data = cls()
                web_component_data.from_data(data)
                web_callback.web_data[id_component_data_name[0]] = web_component_data
                web_component_data_found = True
                break

        if not web_component_data_found:
            log.error(f"Requested WebComponentData {id_component_data_name[1]} NOT found!")

    components: {str, GuiComponent} = web_callback.process()

    response: WebCallbackResponse = WebCallbackResponse()
    for component_id, component in components.items():
        response.add_component(component_id, component)

    return response.to_response()

@web_callback_blueprint.route("/js-actions", methods=["GET"])
def js_actions():
    pass


def get_web_callback() -> Optional[WebCallback]:
    callback_name = request.json.get("callback-name")

    for cls in callback_registry:
        if cls.__name__ == callback_name:
            return cls()

    return None
