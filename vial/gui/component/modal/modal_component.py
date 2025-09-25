from vial.gui.component.gui_component import GuiComponent


class Modal(GuiComponent):
    def __init__(self, component_id: str):
        super().__init__(component_id)
        self._add_style("wrapper", "hidden fixed z-10 pt-16 left-0 top-0 w-full h-full overflow-auto bg-black bg-opacity-80")
        self.size_medium()

    def size_small(self):
        self._add_style("size", "w-2/5")
        return self

    def size_medium(self):
        self._add_style("size", "w-3/5")
        return self

    def size_large(self):
        self._add_style("size", "w-4/5")
        return self

    def add_content(self, content: GuiComponent):
        self._add_child(0, content)
        return self

    def get_template_path(self) -> str:
        return "vial/component/modal/modal.html"