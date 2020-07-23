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
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Union

from grundzeug.container.interface import ReturnMessage, ContinueMessage, NotFoundMessage, ContainerResolutionPlugin, \
    IContainer, RegistrationKey, ContainerRegistration
from grundzeug.container.exceptions import ContainerAlreadyHasRegistrationError
from grundzeug.container.plugins.common import RegistrationBeanResolver


class ContainerAmbiguousResolutionPluginBase(ContainerResolutionPlugin, ABC):
    """
    A base class for container resolution plugins which first collect all compatible registrations in the container
    chain, and then select one based on a rule to be implemented by the deriving class (see
    :py:meth:`~grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase.ContainerAmbiguousResolutionPluginBase.choose_best_candidate`
    )
    """

    @abstractmethod
    def is_registration_key_supported(self, registration_key: RegistrationKey):
        """
        :param registration_key: the registration key that was passed into \
               :py:meth:`~grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase.ContainerAmbiguousResolutionPluginBase.register`.
        :return: ``True`` if the registration key should be handled by this plugin, ``False`` otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def is_registration_compatible_with_requested_key(
            self,
            requested_key: RegistrationKey,
            registered_key: RegistrationKey
    ):
        """
        Called during
        :py:meth:`~grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase.ContainerAmbiguousResolutionPluginBase.resolve_bean_reduce`
        to determine whether a registration should be considered as a candidate for the resolution.

        :param requested_key: The registration key that was requested from the container.
        :param registered_key: The registration key corresponding to the registration being considered.
        :return: ``True`` if ``registered_key`` can be considered a candidate resolution for ``requested_key``, \
                 ``False`` otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def choose_best_candidate(
            self,
            requested_key: RegistrationKey,
            candidates: typing.OrderedDict[RegistrationKey, typing.Tuple[ContainerRegistration, IContainer]]
    ) -> typing.Optional[typing.Tuple[ContainerRegistration, IContainer]]:
        """
        Selects the best matching candidate from the ones collected during the container chain reduction done by
        :py:meth:`~grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase.ContainerAmbiguousResolutionPluginBase.resolve_bean_reduce`
        .

        :param requested_key: The registration key that was requested from the container.
        :param candidates: An ordered dictionary mapping registration keys to registration-container tuples, where the \
                           container is the furthest from the root for the registration key. The order is determined \
                           by the traversal order of the containers during reduction, i.e. the registrations from the \
                           root container come last, while the registrations from the container ``resolve`` was called \
                           on come first.
        :return: One of the values stored in ``candidates``.
        """
        raise NotImplementedError()

    def register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration,
            container: IContainer
    ) -> bool:
        registry = container.get_plugin_storage(self)

        if key in registry:
            raise ContainerAlreadyHasRegistrationError()
        if self.is_registration_key_supported(key):
            registry[key] = registration
            return True
        return False

    def resolve_bean_create_initial_state(
            self,
            key: RegistrationKey,
            container: IContainer
    ) -> Any:
        return OrderedDict()

    def resolve_bean_reduce(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer,
            ancestor_container: IContainer
    ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
        if not self.is_registration_key_supported(key):
            return NotFoundMessage(local_state)

        registry = ancestor_container.get_plugin_storage(self)
        for k, value in registry.items():
            if k in local_state:
                # Compatible object with the same key was already resolved by a descendant container
                continue

            if self.is_registration_compatible_with_requested_key(key, k):
                local_state[k] = (value, container)

        return ContinueMessage(local_state)

    def resolve_bean_postprocess(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer
    ) -> Any:
        if len(local_state) == 0:
            return NotFoundMessage(None)
        tup = self.choose_best_candidate(key, local_state)
        if tup is None:
            return NotFoundMessage(None)
        registration, assoc_container = tup
        return ReturnMessage(RegistrationBeanResolver(registration=registration, container=assoc_container))

    def registrations(
            self,
            container: IContainer
    ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
        registry = container.get_plugin_storage(self)
        return registry.items()


__all__ = ["ContainerAmbiguousResolutionPluginBase"]
