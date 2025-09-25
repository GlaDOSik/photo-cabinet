from abc import ABC, abstractmethod


class WebComponentData(ABC):

    @abstractmethod
    def from_data(self, data: {}):
        pass