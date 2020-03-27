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

from abc import abstractmethod
from pathlib import Path
from typing import TextIO, Union, Any

from typing_extensions import Literal

from grundzeug.config.common import Configurable, ConfigPathT, MISSING, CanonicalConfigPathT


class ConfigurationProvider:
    """
    ConfigurationProviders are queried when configuration values are being resolved.
    """

    @abstractmethod
    def get_value(self, path: CanonicalConfigPathT) -> Union[Any, Literal[MISSING]]:
        """
        :param path: The requested config path (key).
        :return: The requested config value, or :py:const:`~grundzeug.config.common.MISSING` if this provider does \
                 not have the requested config path (key).
        """
        raise NotImplementedError()


class TextParserConfigurationProviderMixin:
    """
    A helper mixin that allows instantiating ConfigurationProviders using files and TextIO.

    Requires the implementing class to have a constructor that takes a single string as an argument.
    """

    @classmethod
    def from_string(cls, string: str) -> ConfigurationProvider:
        """
        Construct the :py:class:`~grundzeug.config.providers.common.ConfigurationProvider` from a string that can
        be directly translated to a configuration hierarchy.

        :param string: The string that will be passed into the class's constructor.
        :return: An instance of the class this method was called on.
        """
        if not issubclass(cls, ConfigurationProvider):
            raise TypeError(f"Classes that extend TextParserConfigurationProviderMixin should also implement "
                            f"grundzeug.config.providers.common.ConfigurationProvider")
        return cls(string)  # type: ignore

    @classmethod
    def from_file(cls, path: Path, encoding=None, errors=None) -> ConfigurationProvider:
        """
        Construct the :py:class:`~grundzeug.config.providers.common.ConfigurationProvider` by reading the file at the
        specified path and passing the contents into the class's constructor.

        Uses :py:meth:`~pathlib.Path.read_text` behind the scenes.

        :param path: The file to read.
        :param encoding: See :py:func:`~builtins.open` for more details.
        :param errors: See :py:func:`~builtins.open` for more details.
        :return: An instance of the class this method was called on.
        """

        return cls.from_string(path.read_text(encoding=encoding, errors=errors))

    @classmethod
    def read(cls, io: TextIO) -> ConfigurationProvider:
        """
        Construct the :py:class:`~grundzeug.config.providers.common.ConfigurationProvider` by reading the specified
        instance of :py:class:`~typing.TextIO` (obtained using :py:func:`~builtins.open` or similar) and passing the
        contents into the class's constructor.

        :param io: the instance of :py:class:`~typing.TextIO` to read and pass into the class's constructor.
        :return: An instance of the class this method was called on.
        """
        return cls.from_string(io.read())


class DictTreeConfigurationProvider(ConfigurationProvider):
    def __init__(self, root: dict):
        """
        A base class for ConfigurationProviders which can represent their contents as an immutable nested dictionary.

        :param root: The root dictionary. A configuration value with the configuration key ("foo", "bar", "baz") will
                     be resolved by indexing ``root`` as follows: ``root["foo"]["bar"]["baz"]``.
        """
        self._dict = root

    def set_value(
            self,
            reference: Union[ConfigPathT, Configurable, Any],
            value
    ):
        if isinstance(reference, Configurable):
            reference = reference.configurable_metadata.full_path
        reference: ConfigPathT = reference

        current_dictionary = self._dict

        for i, name in enumerate(reference[:-1]):
            if name not in current_dictionary:
                current_dictionary[name] = {}
            if not isinstance(current_dictionary[name], dict):
                raise KeyError(f"Could not set the value for configuration key {reference} because the entry at "
                               f"{tuple(reference[:i + 1])} is not a dictionary.")
            current_dictionary = current_dictionary[name]

        current_dictionary[reference[-1]] = value

    def get_value(self, path: ConfigPathT):
        cur = self._dict
        for x in path:
            if x not in cur:
                return MISSING
            cur = cur[x]
        return cur


__all__ = ["ConfigurationProvider", "TextParserConfigurationProviderMixin", "DictTreeConfigurationProvider"]
