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
from typing import Any, Union, TypeVar, Generic

from grundzeug.container.interface import ContainerResolutionPlugin, RegistrationKey, ContainerRegistration, IContainer, \
    ReturnMessage, ContinueMessage, NotFoundMessage, ContractT, BeanResolver
from grundzeug.container.plugins.common import RegistrationBeanResolver

T = TypeVar("T")


class BeanList(Generic[T], tuple, typing.Iterable[T], typing.Sized):
    pass


class _MultiBeanResolver(BeanResolver):
    def __init__(self, resolvers: typing.List[BeanResolver]):
        self.resolvers = resolvers

    def get(self):
        return BeanList((resolver.get() for resolver in self.resolvers))

    @property
    def is_cacheable(self) -> bool:
        return all(x.is_cacheable for x in self.resolvers)


class ContainerBeanListResolutionPlugin(ContainerResolutionPlugin):
    """
    Handles ``BeanList[T]`` contracts. You may register multiple beans with a ``BeanList[T]`` contract.
    When resolving ``BeanList[T]``, all beans that have been registered with the contract will be resolved, including
    those that were registered with ancestor containers.

    Usage:


    .. code-block:: python

        container.register_instance[BeanList[IBean]](Bean1())
        container.register_instance[BeanList[IBean]](Bean2())
        child_container = Container(container)
        child_container.register_instance[BeanList[IBean]](Bean3())
        beans: BeanList = child_container.resolve[BeanList[IBean]]()
        bean3, bean1, bean2 = beans

    """

    def applies_to(self, bean_contract: ContractT):
        return getattr(bean_contract, "__origin__", None) == BeanList

    def register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration,
            container: IContainer
    ) -> bool:
        if not self.applies_to(key.bean_contract):
            return False

        registry = container.get_plugin_storage(self)

        registration_list = registry.get(key, None)
        if registration_list is None:
            registration_list = []
            registry[key] = registration_list
        registration_list.append(registration)
        return True

    def resolve_bean_create_initial_state(
            self,
            key: RegistrationKey,
            container: IContainer
    ) -> Any:
        return []

    def resolve_bean_reduce(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer,
            ancestor_container: IContainer
    ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
        if not self.applies_to(key.bean_contract):
            return NotFoundMessage(local_state)

        bean_resolvers: typing.List[RegistrationBeanResolver] = local_state

        registry = ancestor_container.get_plugin_storage(self)
        registrations = registry[key]

        if key in registry:
            bean_resolvers = bean_resolvers + \
                             [
                                 RegistrationBeanResolver(registration=registration, container=container)
                                 for registration
                                 in registrations
                             ]
        return ContinueMessage(bean_resolvers)

    def resolve_bean_postprocess(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer
    ) -> Union[ReturnMessage, NotFoundMessage]:
        bean_resolvers = local_state
        if not self.applies_to(key.bean_contract):
            return NotFoundMessage(local_state)

        return ReturnMessage(_MultiBeanResolver(bean_resolvers))

    def registrations(
            self,
            container: IContainer
    ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
        registry = container.get_plugin_storage(self)
        for registration_key, registrations in registry.items():
            for registration in registrations:
                yield registration_key, registration


__all__ = ["BeanList", "ContainerBeanListResolutionPlugin"]
