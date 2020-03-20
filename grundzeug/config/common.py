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

import dataclasses
import inspect
from typing import TypeVar, List, Any, Callable, Type, Optional, Generic, Tuple, Union, Set

from grundzeug.container import IContainer
from grundzeug.container.contracts import register_contract_to_type_converter
from grundzeug.container.di import InjectAnnotation
from grundzeug.util.sentinels import make_sentinel

ConfigT = TypeVar("ConfigT")
CanonicalConfigPathT = Tuple[str, ...]
ConfigPathT = Union[CanonicalConfigPathT, List[str]]
ContractVarT = TypeVar("ContractVarT")

CONFIGURATION_METADATA_KEY = "GRUNDZEUG_CONFIGURATION_METADATA"

_MISSING_TYPE, MISSING = make_sentinel()


@dataclasses.dataclass(frozen=True)
class ConfigurationValidationException(Exception):
    """
    Raised by :py:class:`~grundzeug.config.common.Configurable` validation rules when the value being validated has \
    failed to pass the validation rule.
    """
    message: str
    """
    The validation error.
    """
    cause: Optional[Exception] = None
    """
    The exception that caused the validation error.
    """

    def __str__(self) -> str:
        return self.message


@dataclasses.dataclass(frozen=True)
class MissingConfigurationKeysException(Exception):
    missing_keys: Set[CanonicalConfigPathT]
    """
    The missing configuration keys (absolute paths).
    """
    message: str
    """
    The exception's message.
    """

    def __str__(self) -> str:
        return self.message


class Configurable(Generic[ConfigT]):
    def __init__(
            self,
            path: ConfigPathT,
            default: Any = MISSING,
            description: Optional[str] = None,
            clazz: Type[ConfigT] = None
    ):
        """
        A descriptor for configurable properties.

        :param path: The relative path to the configuration value. The full path may be obtained by combining this with\
                     the parent class's path.
        :param default: The default value for this configurable property.
        :param description: The description for this property. For instance, this is used to form the help strings for \
                            :py:class:`~argparse.ArgumentParser`.
        :param clazz: The type of the configuration value.
        """
        self.clazz = clazz
        self.path: CanonicalConfigPathT = tuple(path)
        self.default = default
        self.description = description
        self._owner_class = None
        self._field_name = None

        self.validation_rules: List[Callable[[ConfigT], None]] = []
        if clazz != Any:
            def _assert_isinstance(value):
                if not isinstance(value, clazz):
                    message = f"The Configurable specifies that the value should be an instance of {clazz}, but it's" \
                              f"an instance of {type(value)}."
                    raise ConfigurationValidationException(message, TypeError(message))

            self.validation_rules.append(_assert_isinstance)

    def validation_rule(self, rule: Callable) -> "Configurable":
        """
        Adds a validation rule that will be executed each time this property is requested.

        :param rule: The callable that will be injected and executed. This callable receives the value to be validated \
                     as the first argument (after injection). In the case that the provided value does not pass \
                     the validation rule, this callable should raise a \
                     :py:class:`~grundzeug.config.common.ConfigurationValidationException`.


        """
        configurable = Configurable(self.path, clazz=self.clazz, default=self.default)
        configurable.validation_rules = [*self.validation_rules, rule]
        configurable._owner_class = self._owner_class
        return configurable

    def validate(self, value, container: IContainer) -> None:
        """
        Validates the value by sequentially applying the rules added by
        :py:meth:`~grundzeug.config.common.Configurable.validation_rule`.

        :param value: The value to validate.
        :param container: The container to use for injecting the validation rule functions.
        """
        for rule in self.validation_rules:
            container.inject_func(rule)(value)

    @property
    def full_path(self) -> CanonicalConfigPathT:
        """
        :return: The full path to the configuration value.
        """
        return tuple(self._owner_class.__grundzeug_configuration__.path + self.path)

    @property
    def field_path(self) -> str:
        """
        :return: The Python path to the field described by this Configurable.
        """
        return f"{self._owner_class.__module__}.{self._owner_class.__name__}.{self._field_name}"

    def __class_getitem__(cls, item):
        class _Configurable(Configurable):
            def __init__(
                    self,
                    path: ConfigPathT,
                    default: Any = MISSING,
                    description: Optional[str] = None
            ):
                super(_Configurable, self).__init__(path=path, clazz=item, default=default, description=description)

        return _Configurable


register_contract_to_type_converter(lambda x: x.clazz if isinstance(x, Configurable) else None)  # type: ignore


@dataclasses.dataclass(frozen=True)
class ConfigurationClassMetadata():
    path: CanonicalConfigPathT
    original_class: type


def configuration(path: ConfigPathT):
    """
    A decorator that marks the class as a configuration class.

    Adds a method called `asdict`, which converts configuration class instances into dictionaries.

    :param path: The configuration path (key) prefix for all Configurables in this class.
    """

    def _configurationclass(_cls: type):
        if "__grundzeug_configuration__" in _cls.__dict__:
            _cls = _cls.__dict__["__grundzeug_configuration__"].original_class
        _clsCopy = type(f"{_cls.__name__}___{'_'.join(path)}", (_cls,), {})

        for t in reversed(inspect.getmro(_clsCopy)):
            for k, v in t.__dict__.items():
                if not isinstance(v, Configurable):
                    continue
                v2 = Configurable(clazz=v.clazz, path=tuple(v.path), default=v.default)
                v2._owner_class = _clsCopy
                v2._field_name = k
                v2.validation_rules = list(v.validation_rules)

                setattr(
                    _clsCopy,
                    k,
                    v2
                )
        _clsCopy.__grundzeug_configuration__ = ConfigurationClassMetadata(
            path=tuple(path),
            original_class=_cls
        )

        def _asdict(self):
            res = {}
            for k, v in type(self).__dict__.items():
                if not isinstance(v, Configurable):
                    continue
                res[k] = getattr(self, k)
            return res

        _clsCopy.asdict = _asdict
        return _clsCopy

    return _configurationclass


def inject_config(
        contract: ContractVarT
) -> ContractVarT:
    """
    Indicates that a configuration value should be injected into this parameter.

    Usage:

    .. code-block:: python

        def func(config_value: int = inject_config(ConfigClass.config_value)):
            ...


    :param contract: The :py:class:`~grundzeug.config.common.Configurable` to inject.
    :return: The appropriate :py:class:`~grundzeug.container.di.common.InjectAnnotation`.
    """
    return InjectAnnotation(contract=contract)  # type: ignore


def is_configuration_class(clazz: type) -> bool:
    """
    :param clazz: The class to check.
    :return: True if the class has been processed by :py:func:`~grundzeug.config.common.configuration`, or False \
             otherwise.
    """
    return hasattr(clazz, "__grundzeug_configuration__")


__all__ = ["ConfigT", "CanonicalConfigPathT", "ConfigPathT", "ContractVarT", "CONFIGURATION_METADATA_KEY", "MISSING",
           "ConfigurationValidationException", "MissingConfigurationKeysException", "Configurable",
           "ConfigurationClassMetadata", "configuration", "inject_config", "is_configuration_class"]
