from vial.gui.component.gui_component import GuiComponent


class ModalYesNo(GuiComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id)
        self.component_data["confirm_text"] = "Yes"
        self.component_data["cancel_text"] = "No"
        self._add_style("confirm_style", "")
        self._add_style("cancel_style", "")

    def get_template_path(self) -> str:
        return "vial/component/modal/modal-yes-no.html"

    def set_text(self, text: str):
        self.component_data["text"] = text

    def set_text_style(self, style: str):
        self._add_style("text_style", style)

    def set_confirm_button_text(self, text: str):
        self.component_data["confirm_text"] = text

    def set_confirm_button_style(self, style: str):
        self._add_style("confirm_style", style)

    def set_cancel_button_text(self, text: str):
        self.component_data["cancel_text"] = text

    def set_cancel_button_style(self, style: str):
        self._add_style("cancel_style", style)

    def set_confirm_js_call(self, js_function_call: str):
        self.component_data["confirm_js_call"] = js_function_call

    def set_modal_id(self, modal_id):
        self.component_data["modal_id"] = modal_id