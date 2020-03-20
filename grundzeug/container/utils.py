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
from typing import Type

from grundzeug.container import IContainer, ContainerResolutionPlugin


def lookup_container_plugin_by_type(container: IContainer, plugin_type: Type[ContainerResolutionPlugin]):
    return next(
        plugin
        for plugin
        in container.plugins
        if isinstance(plugin, plugin_type)
    )


__all__ = ["lookup_container_plugin_by_type"]
