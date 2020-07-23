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
from grundzeug.container.interface import BeanResolver, ContainerRegistration, IContainer


class ValueBeanResolver(BeanResolver):
    def __init__(self, value, is_cacheable=True):
        """
        A resolver that always resolves a predetermined value.

        :param value: The bean instance that will be resolved on each query.
        :param is_cacheable: Whether this resolver can be cached, defaults to ``True``.
        """
        self._is_cacheable = is_cacheable
        self.value = value

    def get(self):
        return self.value

    @property
    def is_cacheable(self) -> bool:
        return self._is_cacheable


class RegistrationBeanResolver(BeanResolver):
    def __init__(
            self,
            registration: ContainerRegistration,
            container: IContainer,
            is_cacheable=True
    ):
        """
        A resolver that uses a container registration to resolve a value on each call.
        Differs from ValueBeanResolver because it allows transient registrations to return a new instance each tmie.

        :param registration: The registration to call.
        :param container: The container to call the registration on.
        :param is_cacheable: Whether this resolver can be cached, defaults to ``True``.
        """
        self.container = container
        self._is_cacheable = is_cacheable
        self.registration = registration

    def get(self):
        return self.registration(self.container)

    @property
    def is_cacheable(self) -> bool:
        return self._is_cacheable


__all__ = ["ValueBeanResolver", "RegistrationBeanResolver"]
