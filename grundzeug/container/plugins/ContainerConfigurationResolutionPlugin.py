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

import typing
from dataclasses import dataclass
from typing import Any, Union, TypeVar, Set, Tuple, Dict, Generator

from grundzeug.config import CanonicalConfigPathT, MissingConfigurationKeysException, \
    is_configuration_class
from grundzeug.config.common import Configurable, MISSING
from grundzeug.config.providers.common import ConfigurationProvider
from grundzeug.container.interface import ReturnMessage, ContinueMessage, NotFoundMessage, ContainerResolutionPlugin, \
    IContainer, RegistrationKey, ContainerRegistration, BEAN_NOT_FOUND
from grundzeug.container.plugins import BeanList
from grundzeug.container.plugins.common import ValueBeanResolver
from grundzeug.converters.common import Converter

T = TypeVar("T")


@dataclass
class _ConfigurationValueCollectionState:
    values_left_to_collect: Set[CanonicalConfigPathT]
    collected_values: Dict[CanonicalConfigPathT, str]


class ContainerConfigurationResolutionPlugin(ContainerResolutionPlugin):
    """
    Resolves Grundzeug configuration classes and configurables.
    """

    def applies_to(self, key: RegistrationKey):
        if key.bean_name is not None:
            return False
        return hasattr(key.bean_contract, "__grundzeug_configuration__") \
               or isinstance(key.bean_contract, Configurable)

    def register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration,
            container: IContainer
    ) -> bool:
        if key.bean_contract == BeanList[ConfigurationProvider]:
            registry = container.get_plugin_storage(self)
            if ConfigurationProvider not in registry:
                registry[ConfigurationProvider] = []
            registry[ConfigurationProvider].append(registration)
            return True
        return False

    def _iterate_configuration_class_fields(
            self,
            configuration_clazz: type
    ) -> Generator[Tuple[str, Configurable], None, None]:
        for k, v in configuration_clazz.__dict__.items():
            if not isinstance(v, Configurable):
                continue
            yield k, v

    def _collect_values_create_initial_state(
            self,
            values_to_collect: Set[CanonicalConfigPathT]
    ) -> _ConfigurationValueCollectionState:
        return _ConfigurationValueCollectionState(
            values_left_to_collect=values_to_collect,
            collected_values={}
        )

    def resolve_bean_create_initial_state(
            self,
            key: RegistrationKey,
            container: IContainer
    ) -> Any:
        if not self.applies_to(key):
            return None

        if is_configuration_class(key.bean_contract):
            paths_to_collect = self.get_paths_to_collect(key.bean_contract)
            return self._collect_values_create_initial_state(paths_to_collect)
        else:
            configurable: Configurable = key.bean_contract
            return self._collect_values_create_initial_state({configurable.configurable_metadata.full_path})

    def get_paths_to_collect(self, clazz):
        cur_class_paths = {
            c.configurable_metadata.full_path
            for k, c
            in self._iterate_configuration_class_fields(clazz)
            if not is_configuration_class(c.configurable_metadata.clazz)
        }
        # Add paths from all child configuration classes
        all_paths = cur_class_paths.union(*(
            self.get_paths_to_collect(c.configurable_metadata.clazz)
            for k, c
            in self._iterate_configuration_class_fields(clazz)
            if is_configuration_class(c.configurable_metadata.clazz)
        ))
        return all_paths

    def _collect_values_reduce(
            self,
            state: _ConfigurationValueCollectionState,
            container: IContainer,
            ancestor_container: IContainer
    ) -> _ConfigurationValueCollectionState:
        if len(state.values_left_to_collect) == 0:
            return state
        registry = ancestor_container.get_plugin_storage(self)
        if ConfigurationProvider not in registry:
            return state
        for provider_registration in reversed(registry[ConfigurationProvider]):
            provider_registration: ContainerRegistration = provider_registration
            config_provider: ConfigurationProvider = provider_registration(container)
            to_remove = []
            for to_collect in state.values_left_to_collect:
                res = config_provider.get_value(to_collect)
                if res != MISSING:
                    to_remove.append(to_collect)
                    state.collected_values[to_collect] = res
            state.values_left_to_collect.difference_update(to_remove)
        return state

    def resolve_bean_reduce(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer,
            ancestor_container: IContainer
    ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
        if not self.applies_to(key):
            return NotFoundMessage(local_state)

        local_state: _ConfigurationValueCollectionState = local_state
        local_state = self._collect_values_reduce(local_state, container, ancestor_container)
        if len(local_state.values_left_to_collect) == 0:
            if is_configuration_class(key.bean_contract):
                bean = self._construct_configuration_class(key.bean_contract, local_state, container)
                return ReturnMessage(ValueBeanResolver(bean))
            else:
                configurable: Configurable = key.bean_contract
                value = local_state.collected_values[tuple(configurable.configurable_metadata.full_path)]
                value = self._transform_value(value, configurable, container)
                configurable.validate(value, container)
                return ReturnMessage(ValueBeanResolver(value))
        return ContinueMessage(local_state)

    def resolve_bean_postprocess(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer
    ) -> Any:
        if not self.applies_to(key):
            return NotFoundMessage(None)

        if is_configuration_class(key.bean_contract):
            self._assert_no_missing_configuration_keys(key, local_state)
            bean = self._construct_configuration_class(key.bean_contract, local_state, container)
            return ReturnMessage(ValueBeanResolver(bean))
        else:
            configurable: Configurable = key.bean_contract
            if configurable.configurable_metadata.default == MISSING:
                raise MissingConfigurationKeysException(
                    local_state.values_left_to_collect,
                    f"Could not resolve property {configurable.configurable_metadata.field_path} because there's no "
                    f"config provider satisfying config key {configurable.configurable_metadata.full_path}."
                )
            configurable.validate(configurable.configurable_metadata.default, container)
            return ReturnMessage(ValueBeanResolver(configurable.configurable_metadata.default))

    def _construct_configuration_class(
            self,
            clazz: type,
            local_state: _ConfigurationValueCollectionState,
            container: IContainer
    ) -> Any:
        bean = clazz()
        for k, c in self._iterate_configuration_class_fields(clazz):
            full_path = tuple(c.configurable_metadata.full_path)
            if is_configuration_class(c.configurable_metadata.clazz):
                value = self._construct_configuration_class(c.configurable_metadata.clazz, local_state, container)
            elif full_path in local_state.collected_values:
                value = local_state.collected_values[full_path]
                value = self._transform_value(value, c, container)
            elif c.configurable_metadata.default != MISSING:
                value = c.configurable_metadata.default
            else:
                raise Exception("Impossible situation: this case should've been handled by the "
                                "len(missing_values) != 0 check above!")
            c.validate(value, container)

            setattr(bean, k, value)
        return bean

    def _transform_value(self, value, configurable: Configurable, container: IContainer):
        converter = container.try_resolve[Converter[type(value), configurable.configurable_metadata.clazz]]()
        if converter is BEAN_NOT_FOUND:
            converter = Converter[type(value), configurable.configurable_metadata.clazz].identity()
        return converter(value)

    def _get_paths_of_configurables_with_defaults(self, clazz):
        cur_class_paths = {
            c.configurable_metadata.full_path
            for k, c
            in self._iterate_configuration_class_fields(clazz)
            if c.configurable_metadata.default != MISSING
        }
        # Add paths from all child configuration classes
        all_paths = cur_class_paths.union(*(
            self._get_paths_of_configurables_with_defaults(c.configurable_metadata.clazz)
            for k, c
            in self._iterate_configuration_class_fields(clazz)
            if is_configuration_class(c.configurable_metadata.clazz)
        ))
        return all_paths

    def _assert_no_missing_configuration_keys(
            self,
            key: RegistrationKey,
            local_state: _ConfigurationValueCollectionState
    ) -> None:
        missing_values = local_state.values_left_to_collect \
            .difference(self._get_paths_of_configurables_with_defaults(key.bean_contract))
        if len(missing_values) != 0:
            raise MissingConfigurationKeysException(
                missing_values,
                f"Could not resolve configuration class {key.bean_contract}: the following configuration keys "
                f"are missing: {', '.join((str(x) for x in missing_values))}."
            )

    def registrations(
            self,
            container: IContainer
    ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
        registry = container.get_plugin_storage(self)
        if ConfigurationProvider in registry:
            for registration in registry[ConfigurationProvider]:
                yield BeanList[ConfigurationProvider], registration


__all__ = ["ContainerConfigurationResolutionPlugin"]
