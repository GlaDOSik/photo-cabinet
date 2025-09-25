from typing import Optional

from vial.gui.component.gui_component import GuiComponent


class Empty(GuiComponent):
    def __init__(self, component_id: Optional[str]):
        super().__init__(component_id)

    def get_template_path(self) -> str:
        return "vial/component/empty.html"