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


def set_module(module_name: str):
    """
    A decorator that sets the ``__module__`` of the object.

    Usage example:

    .. code-block:: python

        @set_module("package.subpackage")
        class TestClass(Injector):
            pass

    :param module_name: The desired value for ``__module__``.
    """

    def _set_module(func):
        func.__module__ = module_name
        return func

    return _set_module


__all__ = ["set_module"]
