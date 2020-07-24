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
import uuid
from typing import Any, Optional, Callable, Tuple, TypeVar, Type, Union, overload
from weakref import WeakKeyDictionary, WeakValueDictionary

from grundzeug.container.exceptions import ResolutionFailedError
from grundzeug.container.interface import ReturnMessage, ContinueMessage, NotFoundMessage, \
    ContainerResolutionPlugin, FuncT, IContainer, IContainerRegisterInstanceIndexer, \
    IContainerResolveIndexer, IContainerRegisterFactoryIndexer, IContainerRegisterTypeIndexer, GetBeanProtocol, \
    RegisterInstanceProtocol, RegisterFactoryProtocol, RegistrationKey, ContainerRegistration, \
    ContractT, RegisterTypeProtocol, Injector, BEAN_NOT_FOUND, BEAN_NOT_FOUND_TYPE
from grundzeug.container.registrations import InstanceContainerRegistration, \
    ContainerFactoryContainerRegistration
from grundzeug.util.docs import set_module

BeanT = TypeVar("BeanT")


@set_module("grundzeug.container")
class ContainerResolveIndexer(IContainerResolveIndexer):
    def __init__(self, func: Callable[[ContractT, str], BeanT]):
        self._func = func

    def __getitem__(self, contract: ContractT) -> GetBeanProtocol:
        def __getbean(bean_name: Optional[str] = None):
            return self._func(contract, bean_name)

        return __getbean


@set_module("grundzeug.container")
class ContainerRegisterInstanceIndexer(IContainerRegisterInstanceIndexer):
    def __init__(self, container: "Container"):
        self._container = container

    def __getitem__(
            self,
            contract: ContractT
    ) -> RegisterInstanceProtocol:
        def __register_instance(
                instance: BeanT,
                bean_name: Optional[str] = None
        ) -> "IContainer":
            return self._container._register_instance(
                instance=instance,
                contract=contract,
                bean_name=bean_name,
            )

        return __register_instance

    def __call__(
            self,
            instance: BeanT,
            contract: Optional[ContractT] = None,
            bean_name: Optional[str] = None,
    ) -> "IContainer":
        return self._container._register_instance(
            instance=instance,
            contract=contract,
            bean_name=bean_name,
        )


@set_module("grundzeug.container")
class ContainerRegisterFactoryIndexer(IContainerRegisterFactoryIndexer):
    def __init__(self, container: "Container"):
        self._container = container

    def __getitem__(
            self, contract: ContractT
    ) -> RegisterFactoryProtocol:
        def __register_factory(
                factory: Callable[[], Any],
                bean_name: Optional[str] = None,
                registration_type: Type[ContainerRegistration] = None
        ) -> "IContainer":
            return self._container._register_factory(
                contract=contract,
                factory=factory,
                bean_name=bean_name,
                registration_type=registration_type
            )

        return __register_factory

    def __call__(
            self,
            contract: ContractT,
            factory: Callable[[], Any],
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        return self._container._register_factory(
            contract=contract,
            factory=factory,
            bean_name=bean_name,
            registration_type=registration_type
        )


@set_module("grundzeug.container")
class ContainerRegisterTypeIndexer(IContainerRegisterTypeIndexer):
    def __init__(self, container: "Container"):
        self._container = container

    @overload
    def __getitem__(
            self,
            contract_registration: Tuple[ContractT, Type[BeanT]]
    ) -> RegisterTypeProtocol:
        pass

    @overload
    def __getitem__(
            self,
            contract_registration: ContractT
    ) -> RegisterTypeProtocol:
        pass

    def __getitem__(
            self,
            contract_registration: Union[typing.Tuple[ContractT, Type[BeanT]], ContractT]
    ) -> RegisterTypeProtocol:
        if isinstance(contract_registration, tuple):
            def __register_type(
                    bean_name: Optional[str] = None,
                    registration_type: Type[ContainerRegistration] = None
            ) -> "IContainer":
                return self._container._register_type(
                    contract=contract_registration[0],
                    clazz=contract_registration[1],
                    bean_name=bean_name,
                    registration_type=registration_type
                )

            return __register_type
        else:
            def __register_type(
                    bean_name: Optional[str] = None,
                    registration_type: Type[ContainerRegistration] = None
            ) -> "IContainer":
                return self._container._register_type(
                    contract=contract_registration,
                    clazz=contract_registration,
                    bean_name=bean_name,
                    registration_type=registration_type
                )

            return __register_type

    def __call__(
            self,
            contract: ContractT,
            clazz: Optional[type] = None,
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        return self._container._register_type(
            contract=contract,
            clazz=clazz,
            bean_name=bean_name,
            registration_type=registration_type
        )


@set_module("grundzeug.container")
class ContainerInjector(Injector):
    """
    The implementation for :py:class:`~grundzeug.container.Injector` that is registered by
    :py:class:`~grundzeug.container.Container`.
    """

    def __init__(self, container: "IContainer"):
        self.__container = container

    def inject(self, func: FuncT) -> FuncT:
        from grundzeug.container.di import inject
        return inject(self.__container, func)

    def get_kwargs_to_inject(self, func: FuncT) -> typing.Dict[str, Any]:
        from grundzeug.container.di import get_kwargs_to_inject
        return get_kwargs_to_inject(self.__container, func)


@set_module("grundzeug.container")
class Container(IContainer):
    def __init__(self, parent: Optional["Container"] = None):
        super().__init__()
        self.__uuid = uuid.uuid4()
        self.__children = WeakValueDictionary()
        self.__cache = {}

        self._parent = parent
        if parent is not None:
            parent._register_child(self)

        self._register_instance_indexer = ContainerRegisterInstanceIndexer(self)
        self._register_factory_indexer = ContainerRegisterFactoryIndexer(self)
        self._register_type_indexer = ContainerRegisterTypeIndexer(self)
        self._resolve_indexer = ContainerResolveIndexer(self.resolve_bean)
        self._try_resolve_indexer = ContainerResolveIndexer(self.try_resolve_bean)

        from grundzeug.container.plugins import \
            ContainerBeanListResolutionPlugin, \
            ContainerSingleValueResolutionPlugin, \
            ContainerSpecialResolutionPlugin

        if parent is None:
            self._plugins = [
                ContainerBeanListResolutionPlugin(),
                ContainerSingleValueResolutionPlugin(),
                ContainerSpecialResolutionPlugin()
            ]
        else:
            self._plugins = []

        self._plugin_storage = WeakKeyDictionary()

    def __cache_delete(self, key):
        if key in self.__cache:
            del self.__cache[key]

    def __cache_put(self, key, value):
        self.__cache[key] = value

    @property
    def uuid(self):
        return self.__uuid

    @property
    def children(self) -> typing.List["IContainer"]:
        return list(self.__children.values())

    def _register_child(self, container: IContainer):
        self.__children[container.uuid] = container

    def add_plugin(self, plugin: ContainerResolutionPlugin) -> IContainer:
        if self._parent is not None:
            self._parent.add_plugin(plugin)
        else:
            self._plugins.insert(0, plugin)
        return self

    @property
    def plugins(self):
        if self._parent is not None:
            return self._parent.plugins
        else:
            return self._plugins

    @property
    def parent(self):
        return self._parent

    def _register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration
    ):
        for plugin in self.plugins:
            if plugin.register(
                    key=key,
                    registration=registration,
                    container=self
            ):
                self.__cache_delete(key=key)
                return

    def _register_instance(
            self,
            instance: BeanT,
            contract: Optional[ContractT] = None,
            bean_name: Optional[str] = None
    ) -> "IContainer":
        if contract is None:
            contract = type(instance)
        key = RegistrationKey(contract, bean_name)

        registration = InstanceContainerRegistration(
            container=self,
            key=key,
            instance=instance
        )

        self._register(key, registration)
        return self

    @property
    def register_instance(self) -> IContainerRegisterInstanceIndexer:
        return self._register_instance_indexer

    def _register_factory(
            self,
            contract: ContractT,
            factory: Callable[[], Any],
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        key = RegistrationKey(contract, bean_name)

        if registration_type is None:
            registration_type = ContainerFactoryContainerRegistration

        registration = registration_type(
            container=self,
            key=key,
            factory=factory
        )

        self._register(key, registration)
        return self

    @property
    def register_factory(self) -> IContainerRegisterFactoryIndexer:
        return self._register_factory_indexer

    def _register_type(
            self,
            contract: ContractT,
            clazz: Optional[type] = None,
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        if clazz is None:
            clazz = contract

        self._register_factory(
            contract=contract,
            factory=clazz,
            bean_name=bean_name,
            registration_type=registration_type
        )
        return self

    @property
    def register_type(self) -> IContainerRegisterTypeIndexer:
        return self._register_type_indexer

    def try_resolve_bean(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ) -> Union[BeanT, BEAN_NOT_FOUND_TYPE]:
        if bean_name is None and contract == Container:
            return self

        key = RegistrationKey(contract, bean_name)

        if key in self.__cache:
            return self.__cache[key].get()

        plugins = list(self.plugins)
        states = [
            plugin.resolve_bean_create_initial_state(key, self)
            for plugin
            in plugins
        ]

        current_container = self
        while current_container is not None:
            for i, plugin in enumerate(self.plugins):
                res = plugin.resolve_bean_reduce(key, states[i], self, current_container)

                if isinstance(res, ReturnMessage):
                    resolver = res.resolver
                    if resolver.is_cacheable:
                        self.__cache_put(key, resolver)
                    return resolver.get()
                elif isinstance(res, NotFoundMessage):
                    states[i] = res.state
                elif isinstance(res, ContinueMessage):
                    states[i] = res.state
                    break
                else:
                    raise NotImplementedError()

            current_container = current_container.parent

        for i, plugin in enumerate(self.plugins):
            res = plugin.resolve_bean_postprocess(key, states[i], self)
            if isinstance(res, ReturnMessage):
                resolver = res.resolver
                if resolver.is_cacheable:
                    self.__cache_put(key, resolver)
                return resolver.get()
            elif isinstance(res, NotFoundMessage):
                pass
            else:
                raise NotImplementedError()
        return BEAN_NOT_FOUND

    def resolve_bean(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ) -> BeanT:
        bean = self.try_resolve_bean(contract=contract, bean_name=bean_name)
        if bean is BEAN_NOT_FOUND:
            raise ResolutionFailedError(f"Bean not found: contract={contract}, bean_name={bean_name}")
        return bean

    @property
    def resolve(self) -> IContainerResolveIndexer:
        return self._resolve_indexer

    @property
    def try_resolve(self) -> IContainerResolveIndexer:
        return self._try_resolve_indexer

    def inject(self, func: FuncT) -> FuncT:
        from grundzeug.container.di import inject
        return inject(self, func)

    def get_kwargs_to_inject(self, func: FuncT) -> typing.Dict[str, Any]:
        from grundzeug.container.di import get_kwargs_to_inject
        return get_kwargs_to_inject(self, func)

    def get_plugin_storage(self, plugin: ContainerResolutionPlugin):
        if plugin not in self._plugin_storage:
            self._plugin_storage[plugin] = {}
        return self._plugin_storage[plugin]


__all__ = ["ContainerResolveIndexer", "ContainerRegisterInstanceIndexer", "ContainerRegisterFactoryIndexer",
           "ContainerRegisterTypeIndexer", "ContainerInjector", "Container"]
