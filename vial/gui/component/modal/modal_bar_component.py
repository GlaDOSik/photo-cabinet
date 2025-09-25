from typing import Optional

from vial.gui.component.gui_component import GuiComponent


class ModalBar(GuiComponent):
    def __init__(self, component_id: Optional[str]):
        super().__init__(component_id)

    # TODO - separate OH style from Vial
    def style_default(self):
        self._add_style("bar", "flex justify-between items-center oh-rad-small oh-bgc-light h-10 px-3 gap-x-2 oh-fontc-main")
        return self

    def set_title(self, title: str):
        self.component_data["title"] = title
        return self

    def add_content(self, content_component: GuiComponent):
        self._add_child(0, content_component)
        return self

    def set_bar_style(self, style: str):
        self._add_style("bar", style)
        return self

    def set_modal_id(self, modal_id: str):
        self.component_data["modal_id"] = modal_id
        return self

    def get_template_path(self) -> str:
        return "vial/component/modal/modal-bar.html"