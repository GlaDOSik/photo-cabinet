from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from flask import render_template

from vial.gui.component.component_factory import ComponentRegistry
from service import oh_component_tools # keep it here


class GuiComponent(ABC):
    def __init__(self, component_id: str):
        self.component_id = component_id
        self.component_data = {} # Static data passed to template during rendering
        self.component_variables = {} # Variables passed to template and retrieved for callback
        self.styles = {"wrapper": ""}
        self.slots: Dict[int, List["GuiComponent"]] = {}
        self.parent: Optional[GuiComponent] = None
        self.render_empty: bool = False

    @abstractmethod
    def get_template_path(self) -> str:
        return ""

    def _add_style(self, style_name: str, classes: str):
        self.styles[style_name] = classes

    def _add_child(self, slot_index: int, component: "GuiComponent"):
        if slot_index not in self.slots:
            self.slots[slot_index] = []
        component.parent = self
        self.slots[slot_index].append(component)

    def render(self):
        if self.render_empty:
            return render_template("vial/component/id-wrapper.html", id=self.component_id, component="",
                                   style=self.styles)

        rendered_children = {}
        for slot_index, components in self.slots.items():
            slot_children = []
            for component in components:
                slot_children.append(component.render())
            rendered_children[slot_index] = slot_children

        if self.parent is None or self.component_id is None:
            return render_template(self.get_template_path(), id=self.component_id, data=self.component_data,
                                   style=self.styles, slot=rendered_children, tool=ComponentRegistry.ct)
        else:
            component = render_template(self.get_template_path(), id=self.component_id, data=self.component_data,
                                        style=self.styles, slot=rendered_children, tool=ComponentRegistry.ct)
            return render_template("vial/component/id-wrapper.html", id=self.component_id, component=component, style=self.styles)