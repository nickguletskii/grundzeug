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
from typing import Any, Tuple

import pytest

from grundzeug.container import Container, RegistrationKey, Injector
from grundzeug.container.di import Inject, inject_value
from grundzeug.container.plugins import BeanList, ContainerBeanListResolutionPlugin
from grundzeug.container.plugins.ContainerConverterResolutionPlugin import ContainerConverterResolutionPlugin
from grundzeug.container.utils import lookup_container_plugin_by_type
from grundzeug.converters import Converter
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
        bean: BeanList[IBean] = inject_value[BeanList[IBean]]()
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

    def test_injector_resolution(self):
        container = Container()
        assert isinstance(container.resolve[Injector](), Injector)

    @injectable_func_parametrize_list
    def test_bean_list_injection(self, func):
        container = Container()
        container.register_factory[BeanList[IBean]](lambda: Bean())
        container.register_factory[BeanList[IBean]](lambda: Bean2())

        x, y, z = container.inject(func)(42, kwarg="baz")
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

    def test_converter_resolution(self):
        container = Container()
        container.add_plugin(ContainerConverterResolutionPlugin())

        def _assert_false(x):
            assert False

        container.register_instance[Converter[Any, Any]](_assert_false)
        container.register_instance[Converter[Any, int]](_assert_false)
        container.register_instance[Converter[str, object]](Converter[str, object].identity())
        container.register_instance[Converter[str, int]](lambda x: int(x))

        str_to_int = container.resolve[Converter[str, int]]()
        assert str_to_int("3") == 3

        str_to_obj = container.resolve[Converter[str, object]]()
        assert str_to_obj("3") == "3"
