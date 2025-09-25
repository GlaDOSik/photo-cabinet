from abc import ABC, abstractmethod
from base64 import b64encode
from typing import Dict, Optional

from flask import jsonify

from vial.gui.component.gui_component import GuiComponent
from vial.webcallback.web_component_data import WebComponentData


class WebCallback(ABC):
    def __init__(self):
        self.web_data: Dict[str, WebComponentData] = {}
        self.transient_data = {}

    @abstractmethod
    def process(self) -> {str, GuiComponent}:
        pass

    def set_transient_data(self, key: str, value):
        self.transient_data[key] = value
        return self


class WebCallbackResponse:
    def __init__(self):
        self.redirect_url: Optional[str] = None
        self.components: Optional[Dict] = None

    def do_redirect(self, redirect_url: str):
        self.redirect_url = redirect_url

    def add_component(self, component_id: str, component: GuiComponent):
        if self.components is None:
            self.components = {}

        self.components[component_id] = self._encode_base64_str(component.render())

    def to_response(self):
        if self.redirect_url is not None:
            return jsonify({"redirectUrl": self.redirect_url})
        else:
            return jsonify({"components": self.components})

    def _encode_base64_str(self, str_to_encode: str):
        return b64encode(str_to_encode.encode("utf-8")).decode("utf-8")
