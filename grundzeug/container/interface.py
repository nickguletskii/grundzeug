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
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Type, TypeVar, Any, Union

import typing_extensions

from grundzeug.util.docs import set_module
from grundzeug.util.sentinels import make_sentinel

BeanT = TypeVar("BeanT")
BeanType = Any
FuncT = TypeVar("FuncT")
ContractT = Any

BEAN_NOT_FOUND_TYPE, BEAN_NOT_FOUND = make_sentinel()


@set_module("grundzeug.container")
@dataclass(init=True, repr=True, eq=True, order=True, unsafe_hash=False, frozen=True)
class RegistrationKey:
    """
    Bean registration key. Uniquely identifies a bean within an :py:class:`~grundzeug.container.IContainer`.

    """
    bean_contract: ContractT
    bean_name: Optional[str]


@set_module("grundzeug.container")
class ContainerRegistration(ABC):

    def __init__(
            self,
            container: "IContainer",
            key: RegistrationKey
    ):
        """
        Responsible for creating, storing and destroying the bean or beans that are associated with the registration
        key.

        :param container: The container that this registration is associated with.
        :param key: The key that identifies this registration within the container.
        """
        self.container = container
        self.key = key

    @abstractmethod
    def __call__(self, container: "IContainer") -> Any:
        """
        Construct or retrieve the registered bean.

        :param container: The container that is being queried. This can be the container that \
                          :py:func:`~grundzeug.container.IContainer.resolve_bean` was called on, or one of \
                          its ancestors.
        :return: The registered bean.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class GetBeanProtocol(typing_extensions.Protocol):
    """
    A protocol for a partially applied bean resolution function. The callable that implements this protocol is already
    aware of the requested contract type, but not the bean's name.
    """

    def __call__(self, bean_name: Optional[str] = None):
        """
        :param bean_name: May be ``None``. The optional name of the bean to retrieve.
        :return: The bean associated with the requested bean contract and bean name.
        """
        pass


@set_module("grundzeug.container")
class IContainerResolveIndexer:
    """
    A helper class that helps implement the following syntax:

    .. code-block:: python

        container.resolve[Contract](bean_name="test_bean")

    Here, ``container.resolve[Contract]`` is an instance of \
    :py:class:`~grundzeug.container.IContainerResolveIndexer`.

    """

    @abstractmethod
    def __getitem__(self, contract: ContractT) -> GetBeanProtocol:
        """
        :param contract: The contract to resolve.
        :return: A partially applied bean resolution function that is aware of the requested contract.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class RegisterInstanceProtocol:
    """
    A protocol for a partially applied bean instance registration function. The callable that implements this protocol
    is already aware of the requested contract type, but not the bean itself or its (optional) name.
    """

    def __call__(self, instance: BeanT, bean_name: Optional[str] = None) -> "IContainer":
        """
        Register the specified instance as the implementation of the specified contract.

        :param instance: The instance to register as the implementation for the specified contract.
        :param bean_name: Optional name for this bean.
        :return: The container, for method cascading.
        """
        pass


@set_module("grundzeug.container")
class IContainerRegisterInstanceIndexer:
    @abstractmethod
    def __getitem__(
            self,
            contract: ContractT
    ) -> RegisterInstanceProtocol:
        """
        Register the specified instance as the implementation of the specified contract with an optional name.

        This method partially applies
        :py:meth:`~grundzeug.container.IContainerRegisterInstanceIndexer.__call__`, essentially performing \
        ``functools.partial(container.register_instance, contract=contract)``.


        Usage:

        .. code-block:: python

            container.register_instance[IBean](Bean(), bean_name=optional_name)

        :param contract: The contract to associate the bean with.
        :return: A callable that corresponds to ``container.register_instance[IBean]``. You may call it with the bean \
                 instance and an optional name to register the instance as the implementation for the specified \
                 contract with the specified name (if any).
        """
        raise NotImplementedError()

    @abstractmethod
    def __call__(
            self,
            instance: BeanT,
            contract: Optional[ContractT] = None,
            bean_name: Optional[str] = None,
    ) -> "IContainer":
        """
        Register the specified instance as the implementation of the specified contract with an optional name.

        :param instance: The instance to register as the implementation for the specified contract.
        :param contract: The contract to associate the bean with.
        :param bean_name: An optional name for this bean.
        :return: The container, for method cascading.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class RegisterFactoryProtocol:
    """
    A protocol for a partially applied bean factory registration function. The callable that implements this protocol
    is already aware of the requested contract type, but not the bean's factory or its (optional) name.
    """

    def __call__(
            self,
            factory: typing.Callable[[], typing.Any],
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        """
        Register the specified factory as the implementation of the specified contract.

        :param factory: The factory that can be used to instantiate an instance of the bean.
        :param bean_name: An optional name for this bean.
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often the factory will be executed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will call\
                                    the factory on each resolution, effectively allowing you to return a new instance
                                    each time the bean is requested.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will call\
                                    the factory only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    call the factory once for each descendant-or-self container. Thus, every container \
                                    in the hierarchy will have its own lazily-created instance of the bean.

        :return: The container, for method cascading.
        """
        pass


@set_module("grundzeug.container")
class IContainerRegisterFactoryIndexer:
    @abstractmethod
    def __getitem__(
            self, contract: ContractT
    ) -> RegisterFactoryProtocol:
        """
        Register the  specified factory as the implementation of the specified contract.

        This method partially applies
        :py:meth:`~grundzeug.container.IContainerRegisterFactoryIndexer.__call__`, essentially performing \
        ``functools.partial(container.register_factory, contract=contract)``.


        Usage:

        .. code-block:: python

            container.register_factory[IBean](factory, bean_name=optional_name)

        :param contract: The contract to associate the bean with.
        :return: A callable that corresponds to ``container.register_factory[IBean]``. You may call it with the \
                 factory, an optional name, and/or a registration type to register the instance as the implementation \
                 for the specified contract with the specified name (if any).
        """
        raise NotImplementedError()

    @abstractmethod
    def __call__(
            self,
            contract: ContractT,
            factory: typing.Callable[[], typing.Any],
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        """
        Register the specified factory as the implementation of the specified contract.


        Usage:

        .. code-block:: python

            container.register_factory(IBean, factory, bean_name=optional_name)

        :param contract: The contract to associate the bean with.
        :param factory: The factory that can be used to instantiate an instance of the bean.
        :param bean_name: An optional name for this bean.
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often the factory will be executed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will call\
                                    the factory on each resolution, effectively allowing you to return a new instance
                                    each time the bean is requested.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will call\
                                    the factory only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    call the factory once for each descendant-or-self container. Thus, every container \
                                    in the hierarchy will have its own lazily-created instance of the bean.

        :return: The container, for method cascading.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class RegisterTypeProtocol:
    """
    A protocol for a partially applied bean type registration function. The callable that implements this protocol
    is already aware of the requested contract and implementation types, but not the bean's (optional) name or
    registration type.
    """

    def __call__(
            self,
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        """
        Register the specified bean type as the implementation of the specified contract.

        :param bean_name: An optional name for this bean.
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often an instance of the implementing type will be constructed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will \
                                    create a new instance on each resolution.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will \
                                    create an instance only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    create a separate instance for each descendant-or-self container on-request. Thus, \
                                    every container in the hierarchy will have its own lazily-created instance of the \
                                    bean.

        :return: The container, for method cascading.
        """
        pass


@set_module("grundzeug.container")
class IContainerRegisterTypeIndexer:

    @typing.overload
    def __getitem__(
            self,
            contract_registration: typing.Tuple[ContractT, Type[BeanT]]
    ) -> RegisterTypeProtocol:
        pass

    @typing.overload
    def __getitem__(
            self,
            contract_registration: ContractT
    ) -> RegisterTypeProtocol:
        pass

    @abstractmethod
    def __getitem__(
            self,
            contract_registration: Union[typing.Tuple[ContractT, Type[BeanT]], ContractT]
    ) -> RegisterTypeProtocol:
        """
        Register the specified bean type as the implementation of the specified contract.

        This method partially applies
        :py:meth:`~grundzeug.container.IContainerRegisterTypeIndexer.__call__`, essentially performing \
        ``functools.partial(container.register_type, contract=contract_registration[0], clazz=contract_registration[1])``
        or ``functools.partial(container.register_type, contract=contract_registration, clazz=contract_registration)``.

        Usage:

        .. code-block:: python

            container.register_type[IBean, Bean](bean_name=optional_name)
            container.register_type[Bean](bean_name=optional_name) # The contract is the same as the implementing type

        :param contract_registration: Either a tuple, where the first element is the contract, and the second element \
                                      is the type that will be used to satisfy the contract, or simply a type, which \
                                      will be interpreted both as the contract and the type used to satisfy it.
        :return: A callable that corresponds to ``container.register_type[IBean, Bean]``. You may call it with \
                 an optional name or specify a different registration type. Please see
                 :py:class:`~grundzeug.container.RegisterTypeProtocol` for more details.
        """
        raise NotImplementedError()

    @abstractmethod
    def __call__(
            self,
            contract: ContractT,
            clazz: Optional[type] = None,
            bean_name: Optional[str] = None,
            registration_type: Type[ContainerRegistration] = None
    ) -> "IContainer":
        """
        Register the specified type as the implementation of the specified contract.

        Usage:

        .. code-block:: python

            container.register_type(IBean, Bean, bean_name=optional_name)

        :param contract: The contract to associate the bean with.
        :param clazz: The class that will be instantiated in order to satisfy the contract.
        :param bean_name: An optional name for this bean.
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often an instance of the implementing type will be constructed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will \
                                    create a new instance on each resolution.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will \
                                    create an instance only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    create a separate instance for each descendant-or-self container on-request. Thus, \
                                    every container in the hierarchy will have its own lazily-created instance of the \
                                    bean.

        :return: The container, for method cascading.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class BeanResolver(ABC):
    """
    Returned by container resolution plugins during bean resolution. The purpose of bean resolvers is to provide a
    reusable mechanism for retrieving beans from containers without querying the plugins on subsequent resolutions.
    """

    @abstractmethod
    def get(self):
        """
        :return: The bean for the registration key that this bean resolver is associated with.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def is_cacheable(self) -> bool:
        """
        :return: ``True`` if this bean resolver may be persisted so that subsequent bean resolutions skip querying \
                 plugins entirely.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
@dataclass(frozen=True)
class ReturnMessage:
    """
    Returned by :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or
    :py:meth:`~resolve_bean_postprocess` when the plugin has found the requested bean.
    """

    resolver: BeanResolver
    """
    The resolver that will be used used to retrieve the actual bean. The plugins return resolvers instead of the beans
    themselves because the resolvers are (sometimes) cacheable.
    """


@set_module("grundzeug.container")
@dataclass(frozen=True)
class ContinueMessage:
    """
    Returned by :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` when the plugin has
    determined that it cannot resolve the requested bean at this stage, and no other plugin should be given an
    opportunity to resolve the bean at this stage.
    """
    state: Any
    """
    The state to pass to :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or
    :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_postprocess` during the next stage.
    """


@set_module("grundzeug.container")
@dataclass(frozen=True)
class NotFoundMessage:
    """
    Returned by :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or
    :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_postprocess` when the plugin has
    determined that it cannot resolve the requested bean at this stage, but there's a chance that a different plugin
    may be able to resolve it.
    """
    state: Any
    """
    The state to pass to :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or
    :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_postprocess` during the next stage.
    """


@set_module("grundzeug.container")
class ContainerResolutionPlugin(ABC):
    """
    A base class for container resolution plugins. Allows users to implement custom resolution logic for certain
    contracts.
    """

    @abstractmethod
    def register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration,
            container: "IContainer"
    ) -> bool:
        """
        Register a bean registration with the specified container using the specified key, if the contract can be
        handled by this plugin.

        The plugin may request storage in the container by calling
        :py:meth:`~grundzeug.container.IContainer.get_plugin_storage`

        :param key: The registration key for the bean.
        :param registration: The container registration that will manage bean instantiation.
        :param container: The container to register the bean with.
        :return: ``True`` if the plugin has handled this registration, or ``False`` otherwise.
        """
        raise NotImplementedError()

    def resolve_bean_create_initial_state(
            self,
            key: RegistrationKey,
            container: "IContainer"
    ) -> Any:
        """
        Creates the initial state for the bean resolution procedure. This state will be passed into the
        next call to :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or
        :py:meth:`~resolve_bean_postprocess`.

        For more information, please refer to the documentation regarding container resolution plugins, or read
        the implementation for :py:meth:`~grundzeug.container.container.Container.resolve_bean`.
        #TODO: Create and link the documentation

        :param key: The requested contract and bean name.
        :param container: The container on which :py:func:`~grundzeug.container.IContainer.resolve_bean` was \
                          called on.
        :return: The state to pass into the next call to
                 :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or \
                 :py:meth:`~resolve_bean_postprocess`.
        """
        return None

    @abstractmethod
    def resolve_bean_reduce(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: "IContainer",
            ancestor_container: "IContainer"
    ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
        """
        Executed for each container that is an ancestor of the container
        :py:meth:`~grundzeug.container.container.Container.resolve_bean` was called on, starting with the container
        itself.

        For more information, please refer to the documentation regarding container resolution plugins, or read
        the implementation for :py:meth:`~grundzeug.container.container.Container.resolve_bean`.
        #TODO: Create and link the documentation

        :param key: The requested contract and bean name.
        :param local_state: The state returned by the previous call to \
                            :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or \
                            :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_create_initial_state`.
        :param container: The container on which :py:func:`~grundzeug.container.IContainer.resolve_bean` was \
                          called on.
        :param ancestor_container: The container that is currently being processed by \
                                   :py:func:`~grundzeug.container.IContainer.resolve_bean`. This container is \
                                   an ancestor of the container on which \
                                   :py:func:`~grundzeug.container.IContainer.resolve_bean` was called on, \
                                   or that container itself.
        :return: A message indicating how the bean resolution process must proceed.
        """
        raise NotImplementedError()

    def resolve_bean_postprocess(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: "IContainer"
    ) -> Union[ReturnMessage, NotFoundMessage]:
        """
        Executed after :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` has been
        called for each ancestor-or-self of the container.

        For more information, please refer to the documentation regarding container resolution plugins, or read
        the implementation for :py:meth:`~grundzeug.container.container.Container.resolve_bean`.
        #TODO: Create and link the documentation

        :param key: The requested contract and bean name.
        :param local_state: The state returned by the previous call to \
                            :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_reduce` or \
                            :py:meth:`~grundzeug.container.ContainerResolutionPlugin.resolve_bean_create_initial_state`.
        :param container: The container on which :py:func:`~grundzeug.container.IContainer.resolve_bean` was \
                          called on.
        :return: A message indicating how the bean resolution process must proceed.
        """
        raise NotImplementedError()

    @abstractmethod
    def registrations(
            self,
            container: "IContainer"
    ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
        """
        :param: The container to get the registrations for.
        :return: An iterable of pairs, where the first element is a registration key, and the second element is a \
                 container registration.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class Injector:
    """
    A base interface for classes which are capable of injecting functions with beans from a container or some other
    source.
    """

    @abstractmethod
    def inject(self, func: FuncT) -> FuncT:
        """
        Inject the required beans into the specified function. For instance, let's say we have a function ``foo``
        defined as follows:


        .. code-block:: python

            def foo(arg: int, bean: Inject[IBean]) -> Any:
                ...

        Passing ``foo`` through :py:meth:`~grundzeug.container.Injector.inject` will partially apply
        the function with the requested beans:

        .. code-block:: python

            injected_foo: Callable[[int], Any] = injector.inject(foo)
            foo(42) # No need to pass 'bean'.

        :param func: The function to inject beans into.
        :type func: FuncT
        :return: The injected function.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_kwargs_to_inject(self, func: FuncT) -> typing.Dict[str, Any]:
        """
        Returns the dictionary of kwargs that will be passed into ``func`` on injection.

        If ``func`` is a function, then the following blocks of code should be equivalent:

        .. code-block:: python

            kwargs: typing.Dict[str, Any] = injector.get_kwargs_to_inject(foo)
            foo(42, **kwargs)

        .. code-block:: python

            injected_foo: Callable[[int], Any] = injector.inject(foo)
            foo(42)

        :param func: The function to be introspected.
        :type func: FuncT
        :return: The injected function.
        """
        raise NotImplementedError()


@set_module("grundzeug.container")
class IContainer(Injector):
    @property
    @abstractmethod
    def uuid(self) -> uuid.UUID:
        raise NotImplementedError()

    @property
    @abstractmethod
    def children(self) -> typing.List["IContainer"]:
        raise NotImplementedError()

    @abstractmethod
    def _register_child(self, container: "IContainer"):
        raise NotImplementedError()

    @abstractmethod
    def add_plugin(self, plugin: ContainerResolutionPlugin) -> "IContainer":
        """
        Prepends a plugin to the list of plugins (as returned by
        :py:attr:`~grundzeug.container.IContainer.plugins`).

        Calling this method on a non-root container will register the plugin with the root plugin. Having different
        sets of plugins for different containers in the hierarchy is not supported.

        :param plugin: The plugin to add.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def plugins(self):
        """
        :return: The list of plugins registered with this container hierarchy. Please note that having different \
                 sets of plugins for different containers in the hierarchy is not supported.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def parent(self) -> Optional["IContainer"]:
        """
        :return: The parent container, or ``None`` if this is the root container of the container hierachy.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def register_instance(self) -> IContainerRegisterInstanceIndexer:
        """
        Register the specified instance as the implementation of the specified contract with an optional name.

        Usage:

        .. code-block:: python

            container.register_instance[IBean](Bean(), bean_name=optional_name)
            container.register_instance(Bean(), contract=IBean, bean_name=optional_name) # Equivalent to the line above

        :param instance: The instance to register as the implementation for the specified contract.
        :type instance: typing.Any
        :param contract: The contract to associate the bean with.
        :type contract: typing.Any
        :param bean_name: An optional name for this bean.
        :type bean_name: typing.Optional[str]

        :return: A helper class that implements the syntax described above.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def register_factory(self) -> IContainerRegisterFactoryIndexer:
        """
        Register the specified factory as the implementation of the specified contract.

        Usage:

        .. code-block:: python

            container.register_factory[IBean](factory, bean_name=optional_name)

        :param factory: The factory that can be used to instantiate an instance of the bean.
        :type factory: typing.Callable
        :param bean_name: An optional name for this bean.
        :type bean_name: typing.Optional[str]
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often the factory will be executed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will call\
                                    the factory on each resolution, effectively allowing you to return a new instance
                                    each time the bean is requested.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will call\
                                    the factory only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    call the factory once for each descendant-or-self container. Thus, every container \
                                    in the hierarchy will have its own lazily-created instance of the bean.

        :return: A helper class that implements the syntax described above.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def register_type(self) -> IContainerRegisterTypeIndexer:
        """
        Register the specified type as the implementation of the specified contract.

        Usage:

        .. code-block:: python

            container.register_type[Bean](bean_name=optional_name) # The contract is the same as the implementation
            container.register_type[IBean, Bean](bean_name=optional_name)
            container.register_type(IBean, Bean, bean_name=optional_name) # Equivalent to the line above

        :param contract: The contract to associate the bean with.
        :type contract: typing.Any
        :param clazz: The class that will be instantiated in order to satisfy the contract.
        :type clazz: type
        :param bean_name: An optional name for this bean.
        :type bean_name: typing.Optional[str]
        :param registration_type: The type of the registration. Defaults to  \
                                  :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container`.\

                                  Determines how often an instance of the implementing type will be constructed.

                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Transient` will \
                                    create a new instance on each resolution.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Container` will \
                                    create an instance only once, during the first attempt to resolve this bean. All \
                                    subsequent resolutions for this container and its descendants will yield the same \
                                    instance.
                                  * :py:attr:`~grundzeug.container.registrations.RegistrationTypes.Hierarchical` will \
                                    create a separate instance for each descendant-or-self container on-request. Thus, \
                                    every container in the hierarchy will have its own lazily-created instance of the \
                                    bean.

        :return: A helper class that implements the syntax described above.
        """
        raise NotImplementedError()

    @abstractmethod
    def try_resolve_bean(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ) -> Union[BeanT, BEAN_NOT_FOUND_TYPE]:
        """
        Resolves a bean that is registered with this container or one of the ancestors.

        :param contract: The contract to resolve.
        :param bean_name: An optional name to resolve named beans.
        :return: The requested bean or :py:data:`~grundzeug.container.interface.BEAN_NOT_FOUND`, or \
                 :py:data:`~grundzeug.container.interface.BEAN_NOT_FOUND`.
        :raises Exception: Other exceptions may be thrown when calling the user's factories and constructors.
        """
        raise NotImplementedError()

    @abstractmethod
    def resolve_bean(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ) -> BeanT:
        """
        Resolves a bean that is registered with this container or one of the ancestors.

        :param contract: The contract to resolve.
        :param bean_name: An optional name to resolve named beans.
        :return: The requested bean.
        :raises grundzeug.container.exceptions.ResolutionFailedError: When there aren't any registrations that match \
                                                                      the requested bean.
        :raises Exception: Other exceptions may be thrown when calling the user's factories and constructors.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def resolve(self) -> IContainerResolveIndexer:
        """

        Usage:

        .. code-block:: python

            container.resolve[Contract]()
            container.resolve[Contract](bean_name="test_bean")

        :return:
        """
        raise NotImplementedError()

    @abstractmethod
    def get_plugin_storage(self, plugin: ContainerResolutionPlugin):
        raise NotImplementedError()


__all__ = ["BEAN_NOT_FOUND_TYPE", "BEAN_NOT_FOUND", "RegistrationKey", "ContainerRegistration", "GetBeanProtocol",
           "IContainerResolveIndexer", "RegisterInstanceProtocol", "IContainerRegisterInstanceIndexer",
           "RegisterFactoryProtocol", "IContainerRegisterFactoryIndexer", "RegisterTypeProtocol",
           "IContainerRegisterTypeIndexer", "ReturnMessage", "ContinueMessage", "NotFoundMessage",
           "ContainerResolutionPlugin", "Injector", "IContainer", "ContractT", "BeanResolver"]
