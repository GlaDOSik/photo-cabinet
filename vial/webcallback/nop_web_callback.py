from flask import request

from vial.gui.component.component_factory import ComponentRegistry
from vial.webcallback.web_callback import WebCallback


class NopWebCallback(WebCallback):

    def process(self):
        components = {}
        requested_component_ids: [str] = request.json.get("requested-components")

        for component_id in requested_component_ids:
            components[component_id] = ComponentRegistry.create(component_id, self)

        return components