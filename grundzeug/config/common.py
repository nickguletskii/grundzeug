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
from grundzeug.reflection.types import advanced_isinstance
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


class _ConfigurableMetadata():
    def __init__(
            self,
            path: ConfigPathT,
            default: Any = MISSING,
            description: Optional[str] = None,
            clazz: Type[ConfigT] = None,
            override_config_path: bool = True,
            owner_class=None,
            validation_rules=None
    ):
        self.path: CanonicalConfigPathT = tuple(path)
        self.default = default
        self.description = description
        self.owner_class = owner_class
        self.field_name = None
        self.override_config_path = override_config_path

        if validation_rules is not None:
            self.validation_rules: List[Callable[[ConfigT], None]] = validation_rules
        else:
            self.validation_rules: List[Callable[[ConfigT], None]] = []

        if is_configuration_class(clazz) and override_config_path is not None and owner_class is not None:
            clazz = configuration(self.full_path)(clazz)

        self.clazz = clazz

        if clazz != Any:
            if is_configuration_class(clazz):
                clazz = clazz.__grundzeug_configuration__.original_class

            def _assert_isinstance(value):
                if not advanced_isinstance(value, clazz):
                    message = f"The Configurable specifies that the value should be an instance of {clazz}, but it's" \
                              f"an instance of {type(value)}."
                    raise ConfigurationValidationException(message, TypeError(message))

            self.validation_rules.append(_assert_isinstance)

    @property
    def full_path(self) -> CanonicalConfigPathT:
        """
        :return: The full path to the configuration value.
        """
        return tuple(self.owner_class.__grundzeug_configuration__.path + self.path)

    @property
    def field_path(self) -> str:
        """
        :return: The Python path to the field described by this Configurable.
        """
        if self.field_name is None:
            raise ValueError(f"Attempt to call field_path on a Configurable on a class that hasn't been processed using"
                             f"@configuration.")
        return f"{self.owner_class.__module__}.{self.owner_class.__name__}.{self.field_name}"


class Configurable(Generic[ConfigT]):
    def __init__(
            self,
            path: ConfigPathT,
            default: Any = MISSING,
            description: Optional[str] = None,
            clazz: Type[ConfigT] = None,
            override_config_path: bool = True,
            _owner_class=None,
            _validation_rules=None
    ):
        """
        A descriptor for configurable properties.

        :param path: The relative path to the configuration value. The full path may be obtained by combining this with\
                     the parent class's path.
        :param default: The default value for this configurable property.
        :param description: The description for this property. For instance, this is used to form the help strings for \
                            :py:class:`~argparse.ArgumentParser`.
        :param clazz: The type of the configuration value.
        :param override_config_path: If ``True``, the path of the configuration class will be changed to the full path \
                                     of this configurable. If ``False``, the original path will be retained.
        """
        if is_configuration_class(clazz) and default is not MISSING:
            raise ValueError("If the type of the configurable is a configuration class, the default value can't be "
                             "specified directly. Please specify the defaults for all fields in the configuration"
                             "class instead.")

        self.configurable_metadata = _ConfigurableMetadata(
            path=path,
            default=default,
            description=description,
            clazz=clazz,
            override_config_path=override_config_path,
            owner_class=_owner_class,
            validation_rules=_validation_rules
        )

    def validation_rule(self, rule: Callable) -> "Configurable":
        """
        Adds a validation rule that will be executed each time this property is requested.

        :param rule: The callable that will be injected and executed. This callable receives the value to be validated \
                     as the first argument (after injection). In the case that the provided value does not pass \
                     the validation rule, this callable should raise a \
                     :py:class:`~grundzeug.config.common.ConfigurationValidationException`.


        """
        configurable = Configurable(
            path=self.configurable_metadata.path,
            default=self.configurable_metadata.default,
            description=self.configurable_metadata.description,
            clazz=self.configurable_metadata.clazz,
            override_config_path=self.configurable_metadata.override_config_path,
            _owner_class=self.configurable_metadata.owner_class,
            _validation_rules=[*self.configurable_metadata.validation_rules, rule],
        )
        return configurable

    def validate(self, value, container: IContainer) -> None:
        """
        Validates the value by sequentially applying the rules added by
        :py:meth:`~grundzeug.config.common.Configurable.validation_rule`.

        :param value: The value to validate.
        :param container: The container to use for injecting the validation rule functions.
        """
        for rule in self.configurable_metadata.validation_rules:
            container.inject(rule)(value)

    def __class_getitem__(cls, item):
        class _Configurable(Configurable):
            def __init__(
                    self,
                    path: ConfigPathT,
                    default: Any = MISSING,
                    description: Optional[str] = None,
                    override_config_path: bool = True,
                    _owner_class=None,
                    _validation_rules=None
            ):
                super(_Configurable, self).__init__(
                    path=path,
                    default=default,
                    description=description,
                    clazz=item,
                    override_config_path=override_config_path,
                    _owner_class=_owner_class,
                    _validation_rules=_validation_rules
                )

        return _Configurable

    def __getattribute__(self, name: str):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # Support nested configurable retrieval, e.g. ParentConfigurationClass.child.property
            if is_configuration_class(self.configurable_metadata.owner_class):
                try:
                    configurable_metadata = object.__getattribute__(self, "configurable_metadata")
                    res = getattr(configurable_metadata.clazz, name)
                    if isinstance(res, Configurable):
                        return res
                except AttributeError:
                    pass
            raise


register_contract_to_type_converter(
    lambda x: x.configurable_metadata.clazz if isinstance(x, Configurable) else None)  # type: ignore


@dataclasses.dataclass(frozen=True)
class ConfigurationClassMetadata():
    path: CanonicalConfigPathT
    original_class: type


def configuration(path: Union[ConfigPathT, type]):
    """
    A decorator that marks the class as a configuration class.

    Adds a method called `asdict`, which converts configuration class instances into dictionaries.

    :param path: The configuration path (key) prefix for all Configurables in this class.
    """

    def _configurationclass(_cls: type):
        if "__grundzeug_configuration__" in _cls.__dict__:
            _cls = _cls.__dict__["__grundzeug_configuration__"].original_class
        _clsCopy = type(f"{_cls.__name__}___{'_'.join(path)}", (_cls,), {
            "__grundzeug_configuration__": ConfigurationClassMetadata(
                path=tuple(path),
                original_class=_cls
            )
        })

        for t in reversed(inspect.getmro(_clsCopy)):
            for k, v in t.__dict__.items():
                if not isinstance(v, Configurable):
                    continue
                # Assign a new configurable with the new owner class and field name
                v2 = Configurable(
                    path=v.configurable_metadata.path,
                    default=v.configurable_metadata.default,
                    description=v.configurable_metadata.description,
                    clazz=v.configurable_metadata.clazz,
                    override_config_path=v.configurable_metadata.override_config_path,
                    _owner_class=_clsCopy,
                    _validation_rules=v.configurable_metadata.validation_rules
                )
                v2.configurable_metadata.field_name = k

                setattr(
                    _clsCopy,
                    k,
                    v2
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

    if isinstance(path, type):
        # Handle parameterless decorator, same trick as in dataclasses.dataclass
        cls = path
        path = []
        return _configurationclass(cls)

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
