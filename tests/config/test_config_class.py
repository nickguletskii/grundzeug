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

from grundzeug.config import configuration, Configurable
from grundzeug.config.providers.common import DictTreeConfigurationProvider, ConfigurationProvider
from grundzeug.container import Container
from grundzeug.container.plugins import ContainerConfigurationResolutionPlugin, BeanList


@configuration(["foo", "bar"])
class ExampleConfigurationClass:
    property: int = Configurable[int](["baz"])
    default_property: int = Configurable[int](["boo"], default=3)


@configuration(["foo2", "bar2"])
class ExampleConfigurationClassInheritor(ExampleConfigurationClass):
    pass


class TestConfigClass:
    def test_inheritance_copies_configurable(self):
        assert ExampleConfigurationClass.property.configurable_metadata.full_path == ('foo', 'bar', 'baz')
        assert ExampleConfigurationClassInheritor.property.configurable_metadata.full_path == ('foo2', 'bar2', 'baz')

    @pytest.fixture()
    def container(self):
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

    def test_asdict(self, container):
        config = container.resolve[ExampleConfigurationClass]()
        dct = config.asdict()
        assert isinstance(dct, dict)
        assert dct == {
            "property": 42,
            "default_property": 3
        }
