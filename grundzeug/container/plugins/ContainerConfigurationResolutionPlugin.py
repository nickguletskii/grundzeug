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

import inspect
from dataclasses import dataclass
from typing import Any, Union, TypeVar, Generic, Set, Tuple, Dict, Generator

from grundzeug.config import CanonicalConfigPathT, MissingConfigurationKeysException, \
    is_configuration_class
from grundzeug.config.common import Configurable, MISSING
from grundzeug.config.providers.common import ConfigurationProvider
from grundzeug.container.interface import ReturnMessage, ContinueMessage, NotFoundMessage, ContainerResolutionPlugin, \
    IContainer, RegistrationKey, ContainerRegistration
from grundzeug.container.plugins import BeanList

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
        for t in reversed(inspect.getmro(configuration_clazz)):
            for k, v in t.__dict__.items():
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
            paths_to_collect = {c.full_path for k, c in self._iterate_configuration_class_fields(key.bean_contract)}
            return self._collect_values_create_initial_state(paths_to_collect)
        else:
            configurable: Configurable = key.bean_contract
            return self._collect_values_create_initial_state({configurable.full_path})

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
                bean = self._construct_configuration_class(key, local_state, container)
                return ReturnMessage(bean)
            else:
                configurable: Configurable = key.bean_contract
                configurable.validate(local_state.collected_values[tuple(configurable.full_path)], container)
                return ReturnMessage(local_state.collected_values[tuple(configurable.full_path)])
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
            bean = self._construct_configuration_class(key, local_state, container)
            return ReturnMessage(bean)
        else:
            configurable: Configurable = key.bean_contract
            if configurable.default == MISSING:
                raise MissingConfigurationKeysException(
                    local_state.values_left_to_collect,
                    f"Could not resolve property {key.bean_contract.field_path} because there's no config provider "
                    f"satisfying config key {configurable.full_path}."
                )
            configurable.validate(configurable.default, container)
            return ReturnMessage(configurable.default)

    def _construct_configuration_class(
            self,
            key: RegistrationKey,
            local_state: _ConfigurationValueCollectionState,
            container: IContainer
    ) -> Any:
        bean = key.bean_contract()
        for k, c in self._iterate_configuration_class_fields(key.bean_contract):
            full_path = tuple(c.full_path)
            if full_path in local_state.collected_values:
                value = local_state.collected_values[full_path]
            elif c.default != MISSING:
                value = c.default
            else:
                raise Exception("Impossible situation: this case should've been handled by the "
                                "len(missing_values) != 0 check above!")
            c.validate(value, container)

            setattr(bean, k, value)
        return bean

    def _assert_no_missing_configuration_keys(
            self,
            key: RegistrationKey,
            local_state: _ConfigurationValueCollectionState
    ) -> None:
        missing_values = local_state.values_left_to_collect \
            .difference({
            c.full_path
            for k, c
            in self._iterate_configuration_class_fields(key.bean_contract)
            if c.default != MISSING
        })
        if len(missing_values) != 0:
            raise MissingConfigurationKeysException(
                missing_values,
                f"Could not resolve configuration class {key.bean_contract}: the following configuration keys "
                f"are missing: {', '.join((str(x) for x in missing_values))}."
            )
