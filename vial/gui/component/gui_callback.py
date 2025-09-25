from abc import ABC, abstractmethod
from typing import List

from vial.gui.component.gui_component import GuiComponent

# Callback is used to update some components based on some input components
class Callback(ABC):
    def __init__(self, callback_id: str):
        self.id = callback_id
        self.fetch_components = []

    # What components this callback needs
    def fetch_component(self, component_id):
        self.fetch_components.append(component_id)

    @abstractmethod
    def process(self) -> {str, GuiComponent}:
        pass