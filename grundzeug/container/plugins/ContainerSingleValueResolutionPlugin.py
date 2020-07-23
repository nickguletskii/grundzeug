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
from typing import Any, Union

from grundzeug.container.interface import ReturnMessage, ContinueMessage, NotFoundMessage, ContainerResolutionPlugin, \
    IContainer, RegistrationKey, ContainerRegistration
from grundzeug.container.exceptions import ContainerAlreadyHasRegistrationError
from grundzeug.container.plugins.common import RegistrationBeanResolver


class ContainerSingleValueResolutionPlugin(ContainerResolutionPlugin):
    """
    Default container resolution plugin for Grundzeug containers. Registers and looks up beans by registration keys
    without any bells and whistles. Returns the first matching bean during container chain traversal.
    """
    def register(
            self,
            key: RegistrationKey,
            registration: ContainerRegistration,
            container: IContainer
    ) -> bool:
        registry = container.get_plugin_storage(self)

        if key in registry:
            raise ContainerAlreadyHasRegistrationError()
        registry[key] = registration
        return True

    def resolve_bean_create_initial_state(
            self,
            key: RegistrationKey,
            container: IContainer
    ) -> Any:
        return None

    def resolve_bean_reduce(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer,
            ancestor_container: IContainer
    ) -> Union[ReturnMessage, ContinueMessage, NotFoundMessage]:
        registry = ancestor_container.get_plugin_storage(self)

        if key in registry:
            registration = registry[key]
            return ReturnMessage(RegistrationBeanResolver(registration=registration, container=container))
        return NotFoundMessage(None)

    def resolve_bean_postprocess(
            self,
            key: RegistrationKey,
            local_state: Any,
            container: IContainer
    ) -> Any:
        return NotFoundMessage(None)

    def registrations(
            self,
            container: IContainer
    ) -> typing.Iterable[typing.Tuple[RegistrationKey, ContainerRegistration]]:
        registry = container.get_plugin_storage(self)
        return registry.items()


__all__ = ["ContainerSingleValueResolutionPlugin"]
