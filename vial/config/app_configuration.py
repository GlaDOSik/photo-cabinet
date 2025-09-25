import json
import os
from typing import Any, Optional

from root import ROOT_DIR
from vial.config.invalid_app_configuration_exception import InvalidAppConfigurationException


class AppConfig:

    def __init__(self):
        with open(os.path.join(ROOT_DIR, "config.json")) as config_file:
            self.config_dict = json.load(config_file)

    def get(self, config_data: []) -> Any:
        """
        Shortcut for get_configuration
        """
        return self.get_configuration(config_data)

    def get_configuration(self, config_data: []) -> Any:
        """
        Return value of configuration specified by argument ConfigurationProperty. The value is either from config.json
        or default value if defined. If the value isn't in JSON and no default value is specified, InvalidAppConfigurationException is raised.
        :param config_property:
        :return:
        """
        if len(config_data) != 2:
            raise InvalidAppConfigurationException("", "Invalid input config data")

        property_val = self._find_property(config_data[0])

        if property_val is not None:
            return property_val

        if config_data[1] is not None:
            return config_data[1]

        raise InvalidAppConfigurationException(config_data[0], "Property has no default value nor is in config.json.")

    def is_defaulting(self, config_data: []) -> bool:
        """
        Return true if the property value isn't in the JSON file and the default value is defined.
        Return false in all other cases.
        :param config_property:
        :return:
        """
        property_val = self._find_property(config_data[0])
        return property_val is None and config_data[1] is not None

    def _find_property(self, config_path: str) -> Optional[str]:
        split_path = config_path.split(".")
        property_val = self.config_dict.get(split_path[0])

        if len(split_path) > 1:
            for property_path in split_path[1:]:
                try:
                    if property_val is not None:
                        property_val = property_val.get(property_path)
                except AttributeError as aex:
                    raise InvalidAppConfigurationException(config_path, "Invalid property path in the JSON") from aex

        return property_val
