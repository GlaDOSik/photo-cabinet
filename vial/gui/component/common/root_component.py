from vial.gui.component.gui_component import GuiComponent
from vial.config import app_config
from vial.config import vial_configuration


class Root(GuiComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id)
        self.css = []
        self.js_after_load = []
        self.component_data["server_url"] = app_config.get_configuration(vial_configuration.SERVER_URL)

    def get_template_path(self) -> str:
        return "vial/component/root.html"

    def set_title(self, page_title: str):
        self.component_data["title"] = page_title
        return self

    def add_content(self, component: GuiComponent):
        self._add_child(0, component)
        return self

    def get_content(self):
        return self.slots[0]

    def add_css(self, css_url: str):
        css = self.component_data.get("css")
        if css is None:
            css = []
            self.component_data["css"] = css
        css.append(css_url)
        return self

    def add_js_url(self, js_url: str):
        js = self.component_data.get("js")
        if js is None:
            js = []
            self.component_data["js"] = js
        js.append(js_url)
        return self

    def add_js_after_load(self, js_func: str):
        self.js_after_load.append(js_func)

        complete_js = ""
        for js in self.js_after_load:
            complete_js = complete_js + js + "\n"

        self.component_data["js_after_load"] = complete_js
        return self