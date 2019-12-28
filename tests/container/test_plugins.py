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
import pytest

from grundzeug.container import Container, RegistrationKey
from grundzeug.container.di import Inject, inject
from grundzeug.container.plugins import BeanList, Tuple, ContainerConfigurationResolutionPlugin, \
    ContainerBeanListResolutionPlugin
from grundzeug.container.utils import lookup_container_plugin_by_type
from tests.container.test_di import IBean


class Bean(IBean):
    @property
    def foo(self):
        return "bar"


class Bean2(IBean):
    @property
    def foo(self):
        return "baz"


def injectable_func_type_list(
        arg: int,
        kwarg: str,
        bean: Inject[BeanList[IBean]]
) -> Tuple[int, str, BeanList[IBean]]:
    return arg, kwarg, bean


def injectable_func_field_list(
        arg: int,
        kwarg: str,
        bean: BeanList[IBean] = inject[BeanList[IBean]]()
) -> Tuple[int, str, BeanList[IBean]]:
    return arg, kwarg, bean


injectable_func_parametrize_list = pytest.mark.parametrize(
    "func",
    [
        injectable_func_type_list,
        injectable_func_field_list
    ],
)


class TestContainerResolutionPlugins:

    @injectable_func_parametrize_list
    def test_bean_list_injection(self, func):
        container = Container()
        container.register_factory[BeanList[IBean]](lambda: Bean())
        container.register_factory[BeanList[IBean]](lambda: Bean2())

        x, y, z = container.inject_func(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert isinstance(z, BeanList)
        assert len(z) == 2
        assert {v.foo for v in z} == {"bar", "baz"}

    def test_bean_list_plugin_returns_registrations(self):
        container = Container()
        container.register_factory[BeanList[IBean]](lambda: Bean())
        container.register_factory[BeanList[IBean]](lambda: Bean2())
        plugin = lookup_container_plugin_by_type(container, ContainerBeanListResolutionPlugin)
        registrations = list(plugin.registrations(container))
        assert len(registrations) == 2
        for registration_key, registration in registrations:
            assert isinstance(registration_key, RegistrationKey)
