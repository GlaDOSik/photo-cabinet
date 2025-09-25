from vial.gui.component.gui_component import GuiComponent


class Button(GuiComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id)
        self.text = ""

    def set_text(self, text: str):
        self.component_data["text"] = text
        return self

    def set_style(self, classes: str):
        self._add_style("button", classes)
        return self

    def get_template_path(self) -> str:
        return "vial/component/button/button.html"
