import inspect
from argparse import ArgumentParser
from typing import Tuple, List

import pytest
from typing_extensions import Annotated

from grundzeug.config import configuration, Configurable, inject_config, MissingConfigurationKeysException
from grundzeug.config.providers.argparse import ArgParseConfigurationProvider
from grundzeug.config.providers.common import DictTreeConfigurationProvider, ConfigurationProvider
from grundzeug.container import InstanceContainerRegistration
from grundzeug.container.impl import Container
from grundzeug.container.di import Inject, inject, inject_func
from grundzeug.container.plugins import BeanList
from grundzeug.container.plugins.ContainerConfigurationResolutionPlugin import ContainerConfigurationResolutionPlugin
from grundzeug.container.utils import lookup_container_plugin_by_type


@configuration(["foo", "bar"])
class ExampleConfigurationClass:
    property: int = Configurable[int](["baz"], description="TMPTMP")
    default_property: int = Configurable[int](["boo"], default=3)


def injectable_func_type(
        arg: int,
        kwarg: str,
        prop: Inject[ExampleConfigurationClass.property]
) -> Tuple[int, str, int]:
    return arg, kwarg, prop


def injectable_func_field(
        arg: int,
        kwarg: str,
        prop: int = inject_config(ExampleConfigurationClass.property)
) -> Tuple[int, str, int]:
    return arg, kwarg, prop


injectable_func_parametrize = pytest.mark.parametrize(
    "func",
    [
        injectable_func_type,
        injectable_func_field
    ],
)


class TestConfig:
    @pytest.fixture()
    def full_container(self):
        container = Container()
        container.add_plugin(ContainerConfigurationResolutionPlugin())
        container.register_instance[BeanList[ConfigurationProvider]](
            DictTreeConfigurationProvider({
                "foo": {
                    "bar": {
                        "baz": 42,
                        "boo": 32
                    }
                }
            })
        )
        return container

    def test_full_container_configuration_providers(self, full_container):
        configuration_plugin = lookup_container_plugin_by_type(full_container, ContainerConfigurationResolutionPlugin)

        registrations = list(configuration_plugin.registrations(full_container))
        assert len(registrations) == 1
        registration_key, registration = registrations[0]
        assert registration_key == BeanList[ConfigurationProvider]
        assert isinstance(registration, InstanceContainerRegistration)

    @pytest.fixture()
    def full_container_child(self, full_container):
        full_container_child = Container(full_container)
        full_container_child.register_instance[BeanList[ConfigurationProvider]](
            DictTreeConfigurationProvider({
                "foo": {
                    "bar": {
                        "baz": 62
                    }
                }
            })
        )
        return full_container_child

    def test_full_container_child_configuration_providers(self, full_container_child):
        configuration_plugin = lookup_container_plugin_by_type(full_container_child,
                                                               ContainerConfigurationResolutionPlugin)

        parent_registrations = list(configuration_plugin.registrations(full_container_child.parent))
        assert len(parent_registrations) == 1
        parent_registration_key, parent_registration = parent_registrations[0]
        assert parent_registration_key == BeanList[ConfigurationProvider]
        assert isinstance(parent_registration, InstanceContainerRegistration)

        child_registrations = list(configuration_plugin.registrations(full_container_child))
        assert len(child_registrations) == 1
        child_registration_key, child_registration = child_registrations[0]
        assert child_registration_key == BeanList[ConfigurationProvider]
        assert isinstance(child_registration, InstanceContainerRegistration)

        assert parent_registration != child_registration

    @pytest.fixture()
    def container_lacks_required_key(self):
        container = Container()
        container.add_plugin(ContainerConfigurationResolutionPlugin())
        container.register_instance[BeanList[ConfigurationProvider]](
            DictTreeConfigurationProvider({
                "foo": {
                    "bar": {
                        "boo": 32
                    }
                }
            })
        )
        return container

    @pytest.fixture()
    def container_lacks_key_with_default(self):
        container = Container()
        container.add_plugin(ContainerConfigurationResolutionPlugin())
        container.register_instance[BeanList[ConfigurationProvider]](
            DictTreeConfigurationProvider({
                "foo": {
                    "bar": {
                        "baz": 42
                    }
                }
            })
        )
        return container

    @injectable_func_parametrize
    def test_func_configuration_field_injection(self, func, full_container):
        x, y, z = inject_func(full_container, func)(56, kwarg="baz")
        assert x == 56
        assert y == "baz"
        assert z == 42

    def test_configuration_field_override_in_full_container_child(self, full_container, full_container_child):
        assert full_container.resolve[ExampleConfigurationClass.property]() == 42
        assert full_container.resolve[ExampleConfigurationClass.default_property]() == 32
        assert full_container_child.resolve[ExampleConfigurationClass.property]() == 62
        assert full_container_child.resolve[ExampleConfigurationClass.default_property]() == 32

    def test_configuration_class_field_override_in_full_container_child(self, full_container, full_container_child):
        bean_from_root_container = full_container.resolve[ExampleConfigurationClass]()
        bean_from_child_container = full_container_child.resolve[ExampleConfigurationClass]()
        assert bean_from_root_container.property == 42
        assert bean_from_root_container.default_property == 32
        assert bean_from_child_container.property == 62
        assert bean_from_child_container.default_property == 32

    def test_configuration_field_missing(self, container_lacks_required_key):
        with pytest.raises(MissingConfigurationKeysException):
            container_lacks_required_key.resolve[ExampleConfigurationClass.property]()

    def test_configuration_class_field_missing(self, container_lacks_required_key):
        with pytest.raises(MissingConfigurationKeysException):
            container_lacks_required_key.resolve[ExampleConfigurationClass]()

    def test_configuration_field_default(self, container_lacks_key_with_default):
        assert container_lacks_key_with_default.resolve[ExampleConfigurationClass.default_property]() == 3

    def test_configuration_class_field_default(self, container_lacks_key_with_default):
        assert container_lacks_key_with_default.resolve[ExampleConfigurationClass]().default_property == 3
