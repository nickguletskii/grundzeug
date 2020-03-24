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

import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar

from grundzeug.container.interface import IContainer, ContractT


class TypeIntrospector(ABC):
    @abstractmethod
    def inject_fields(self, type_, instance, container: IContainer):
        raise NotImplementedError()

    @abstractmethod
    def get_kwargs_to_inject(self, func, signature: inspect.Signature, container: IContainer) -> Dict[str, Any]:
        raise NotImplementedError()


_type_introspectors: List[TypeIntrospector] = []


def register_type_introspector(type_introspector: TypeIntrospector):
    _type_introspectors.append(type_introspector)


class InjectAnnotation:
    def __init__(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ):
        self.bean_contract = contract
        self.bean_name = bean_name
        self.__origin__ = contract
        self.__args__ = ()
        self.__parameters__ = ()
        self.__module__ = contract.__module__

    def __class_getitem__(
            cls,
            contract: ContractT
    ):
        return InjectAnnotation(contract=contract, bean_name=None)

    def __mro_entries__(self, bases):
        return self.__origin__.__mro_entries__(bases)

    def __instancecheck__(self, obj):
        return self.__subclasscheck__(type(obj))

    def __subclasscheck__(self, cls):
        return issubclass(cls, self.__origin__)

    def named(self, bean_name: str):
        return InjectAnnotation(contract=self.bean_contract, bean_name=bean_name)


ContractVarT = TypeVar("ContractVarT")


class InjectIndexer:
    def __getitem__(self, contract: ContractT):
        class _InjectAnnotation(InjectAnnotation):
            def __call__(self, bean_name: Optional[str] = None):
                return InjectAnnotation(contract=contract, bean_name=bean_name)

        return _InjectAnnotation(contract=contract)

    def __call__(
            self,
            contract: ContractT,
            bean_name: Optional[str] = None
    ):
        return InjectAnnotation(contract=contract, bean_name=bean_name)


inject_value = InjectIndexer()

__all__ = ["TypeIntrospector", "register_type_introspector", "InjectAnnotation", "InjectIndexer", "inject_value"]
