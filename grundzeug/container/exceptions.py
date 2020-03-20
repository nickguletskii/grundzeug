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

class ContainerAlreadyHasRegistrationError(Exception):
    """
    Thrown by implementations of :py:class:`~grundzeug.container.interface.ContainerResolutionPlugin` when an attempt
    to register a bean has been made, but a bean with the same key has already been registered and the plugin does not
    support multiple bean registrations for that key.
    """
    pass


class ResolutionFailedError(Exception):
    """
    Thrown by :py:meth:`~grundzeug.container.impl.Container.resolve_bean` when all plugins
    (:py:class:`~grundzeug.container.interface.ContainerResolutionPlugin`) have determined that they can't resolve
    the requested bean.
    """
    pass


__all__ = ["ContainerAlreadyHasRegistrationError", "ResolutionFailedError"]
