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

from enum import Enum
from typing import Any, Callable
from weakref import WeakKeyDictionary

from grundzeug.container.interface import ContainerRegistration, RegistrationKey, IContainer


class InstanceContainerRegistration(ContainerRegistration):
    """
    Returns the same instance each time the bean is being resolved.
    """

    def __init__(
            self,
            container: IContainer,
            key: RegistrationKey,
            instance: Any
    ):
        super().__init__(container, key)
        self.instance = instance

    def __call__(self, container: IContainer) -> Any:
        return self.instance


class ContainerFactoryContainerRegistration(ContainerRegistration):
    """
    Creates a new instance of the bean on the first attempt to resolve this bean. All subsequent resolutions for this
    container and its descendants will yield the same instance.
    """

    def __init__(
            self,
            container: IContainer,
            key: RegistrationKey,
            factory: Callable[[], Any]
    ):
        super().__init__(container, key)
        self.factory = factory
        self._registered = False
        self._value = None

    def __call__(self, container: IContainer) -> Any:
        if not self._registered:
            self._registered = True
            self._value = self.container.inject(self.factory)()
        return self._value


class TransientFactoryContainerRegistration(ContainerRegistration):
    """
    Instantiates a new bean each time the bean is being resolved.
    """

    def __init__(
            self,
            container: IContainer,
            key: RegistrationKey,
            factory: Callable[[], Any]
    ):
        super().__init__(container, key)
        self.factory = factory

    def __call__(self, container: IContainer) -> Any:
        return container.inject(self.factory)()


class HierarchicalFactoryContainerRegistration(ContainerRegistration):
    """
    Creates and stores a new instance of the bean for each container in the hierarchy. Therefore, attempting to resolve
    the bean from different containers will yield different containers, while resolving the bean from a single container
    will always yield the same instance.
    """

    def __init__(
            self,
            container: IContainer,
            key: RegistrationKey,
            factory: Callable[[], Any]
    ):
        super().__init__(container, key)
        self.factory = factory
        self._values = WeakKeyDictionary()

    def __call__(self, container: IContainer) -> Any:
        if not container in self._values:
            self._values[container] = container.inject(self.factory)()
        return self._values[container]


class RegistrationTypes(Enum):
    Container = ContainerFactoryContainerRegistration
    """
    Creates a new instance of the bean on the first attempt to resolve this bean. All subsequent resolutions for this
    container and its descendants will yield the same instance.
    """

    Transient = TransientFactoryContainerRegistration
    """
    Instantiates a new bean each time the bean is being resolved.
    """

    Hierarchical = HierarchicalFactoryContainerRegistration
    """
    Creates and stores a new instance of the bean for each container in the hierarchy. Therefore, attempting to resolve
    the bean from different containers will yield different containers, while resolving the bean from a single container
    will always yield the same instance.
    """

    Instance = InstanceContainerRegistration
    """
    Returns the same instance each time the bean is being resolved.
    """


__all__ = ["InstanceContainerRegistration", "ContainerFactoryContainerRegistration",
           "TransientFactoryContainerRegistration", "HierarchicalFactoryContainerRegistration", "RegistrationTypes"]
