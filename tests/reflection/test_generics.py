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
from typing import Generic, TypeVar

from grundzeug.reflection.generics import generic_accessor, generic_aware, get_type_arguments

T = TypeVar("T")


@generic_aware
class _GenericClass(Generic[T]):
    generic_T = generic_accessor(T)


class _DerivedGenericClass(_GenericClass):
    pass


@generic_aware
class _GenericClassWithMethod(Generic[T]):
    @classmethod
    def foo(cls):
        return get_type_arguments(cls)[T]


class _DerivedGenericClassWithMethod(_GenericClassWithMethod):
    pass


class TestGenerics:
    def test_generic_accessor(self):
        cls1 = _GenericClass[int]
        cls2 = _GenericClass[str]
        assert cls1.generic_T == int
        assert cls2.generic_T == str

    def test_generic_accessor_on_derived_class(self):
        cls1 = _DerivedGenericClass[int]
        cls2 = _DerivedGenericClass[str]
        assert cls1.generic_T == int
        assert cls2.generic_T == str

    def test_generic_classmethod(self):
        cls1 = _GenericClassWithMethod[int]
        cls2 = _GenericClassWithMethod[str]
        assert cls1.foo() == int
        assert cls2.foo() == str

    def test_derived_generic_classmethod(self):
        cls1 = _DerivedGenericClassWithMethod[int]
        cls2 = _DerivedGenericClassWithMethod[str]
        assert cls1.foo() == int
        assert cls2.foo() == str

    def test_get_type_arguments(self):
        T1 = TypeVar("T1")
        T2 = TypeVar("T2")
        T3 = TypeVar("T3")
        T4 = TypeVar("T4")
        T5 = TypeVar("T5")

        class _GenericBase1(Generic[T1, T2]):
            pass

        class _GenericBase2(Generic[T3, T4]):
            pass

        class _GenericClass(_GenericBase1[T1, T2], _GenericBase2[str, T4], Generic[T1, T2, T4, T5]):
            pass

        assert get_type_arguments(_GenericClass[float, list, bool, int]) == {
            T1: float,
            T2: list,
            T4: bool,
            T5: int
        }
