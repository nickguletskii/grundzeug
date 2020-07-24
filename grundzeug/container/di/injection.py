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

import functools
import inspect
from typing import Any

from grundzeug.container.interface import IContainer, ContractT
from grundzeug.container.di.common import _type_introspectors
from grundzeug.util.collections import dictionary_union


def injectable(cls: ContractT) -> ContractT:
    class __wrapper(cls):
        def __init__(self, __grundzeug_container: IContainer, *args, **kwargs):
            inject_fields(__grundzeug_container, self)
            inject(__grundzeug_container, super().__init__)(*args, **kwargs)

    setattr(cls, "__injectable__", __wrapper)
    return cls


def inject_fields(container: IContainer, instance: Any):
    for t in reversed(inspect.getmro(type(instance))):
        for type_introspector in _type_introspectors:
            type_introspector.inject_fields(t, instance, container)


def inject(container: IContainer, func):
    if inspect.isclass(func) and hasattr(func, "__injectable__"):
        func = functools.partial(func.__injectable__, container)
    else:
        to_inject = get_kwargs_to_inject(container, func)
        func = functools.partial(func, **to_inject)
    return func


def get_kwargs_to_inject(container, func):
    sig = inspect.signature(func)
    to_inject = dictionary_union(
        *(
            type_introspector.get_kwargs_to_inject(
                func=func,
                signature=sig,
                container=container
            )
            for type_introspector
            in _type_introspectors
        )
    )
    return to_inject


__all__ = ["injectable", "inject_fields", "inject", "get_kwargs_to_inject"]
