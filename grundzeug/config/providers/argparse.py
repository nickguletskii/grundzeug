#  Copyright 2019 Nick Guletskii
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from argparse import ArgumentParser
from typing import Type, Set, Dict, Any

from grundzeug.config.common import ConfigT, Configurable, ConfigPathT, MISSING
from grundzeug.config.providers.common import ConfigurationProvider


class ArgParseConfigurationProvider(ConfigurationProvider):
    def __init__(self, prefix: str = "D"):
        self.prefix = prefix
        self._managed_configurations: Set[Type] = set()
        self._dict: Dict[str, Any] = {}

    def manage_configuration(self, config_type: Type[ConfigT]):
        assert hasattr(config_type, "__grundzeug_configuration__")
        self._managed_configurations.add(config_type)

    def register_arguments(self, argument_parser: ArgumentParser):
        for config_type in self._managed_configurations:
            for k, v in config_type.__dict__.items():
                if not isinstance(v, Configurable):
                    continue
                full_path_joined = ".".join(v.configurable_metadata.full_path)
                argument_parser.add_argument(
                    f"--{self.prefix}{full_path_joined}",
                    default=MISSING,
                    type=v.configurable_metadata.clazz,
                    help=v.configurable_metadata.description,
                    required=False
                )

    def process_parsed_arguments(self, value):
        for config_type in self._managed_configurations:
            for k, v in config_type.__dict__.items():
                if not isinstance(v, Configurable):
                    continue
                full_path_joined = ".".join(v.configurable_metadata.full_path)
                val = getattr(value, self.prefix + full_path_joined)
                if val == MISSING:
                    continue
                self._dict[full_path_joined] = val

    def get_value(self, path: ConfigPathT):
        joined_path = ".".join(path)
        if joined_path in self._dict:
            return self._dict[joined_path]
        return MISSING


__all__ = ["ArgParseConfigurationProvider"]
