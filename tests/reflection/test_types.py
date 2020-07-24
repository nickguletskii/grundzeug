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
import typing
from typing import Tuple, Optional, Any

from grundzeug.reflection.types import can_substitute, is_weak_overload_of, advanced_isinstance


class BaseClass1:
    pass


class BaseClass2:
    pass


class DerivedClass1(BaseClass1):
    pass


class DerivedClass2(BaseClass2):
    pass


T1 = typing.TypeVar("T1")
T2 = typing.TypeVar("T2")


class GenericClass(typing.Generic[T1]):
    pass


class DerivedGenericClass(typing.Generic[T2, T1], GenericClass[T1]):
    pass


class CallableClass:
    def __call__(self, test: str, test2: float) -> int:
        pass


class TestTypes:

    def test_can_substitute_to_any(self):
        assert can_substitute(str, Any)
        assert can_substitute(type, Any)
        assert can_substitute(None, Any)
        assert can_substitute(Tuple[DerivedClass1, DerivedClass2], Any)

    def test_can_substitute_to_none_optional(self):
        assert can_substitute(None, Optional[str])

    def test_can_substitute_to_tuples(self):
        assert can_substitute(Tuple[DerivedClass1], Tuple[BaseClass1])
        assert can_substitute(Tuple[DerivedClass1], tuple)
        assert can_substitute(Tuple[DerivedClass1, DerivedClass2], Tuple[BaseClass1, BaseClass2])
        assert can_substitute(Tuple[DerivedClass1, BaseClass2], Tuple[BaseClass1, BaseClass2])
        assert not can_substitute(Tuple[BaseClass1, BaseClass2], Tuple[DerivedClass1, DerivedClass2])
        assert not can_substitute(Tuple[BaseClass1, BaseClass2], Tuple[DerivedClass1, BaseClass2])

    def test_can_substitute_to_generic_class(self):
        assert can_substitute(GenericClass[int], GenericClass[T1])
        assert not can_substitute(GenericClass[T1], GenericClass[int])
        assert can_substitute(GenericClass[int], GenericClass)
        assert not can_substitute(GenericClass, GenericClass[int])

    def test_can_substitute_to_generic_subclass(self):
        assert can_substitute(DerivedGenericClass[str, int], GenericClass[int])
        assert not can_substitute(DerivedGenericClass[int, str], GenericClass[int])

    def test_can_substitute_to_generic_class_bound(self):
        TB = typing.TypeVar("TB", bound=BaseClass1)

        class GenericClassBound(typing.Generic[TB]):
            pass

        assert can_substitute(GenericClassBound[DerivedClass1], GenericClassBound[TB])
        assert not can_substitute(GenericClassBound[TB], GenericClassBound[DerivedClass1])
        assert can_substitute(GenericClassBound[DerivedClass1], GenericClassBound)
        assert not can_substitute(GenericClassBound, GenericClassBound[DerivedClass1])

    def test_can_substitute_to_generic_class_constraint(self):
        TC = typing.TypeVar("TC", BaseClass1, int)

        class GenericClassConstraint(typing.Generic[TC]):
            pass

        assert can_substitute(GenericClassConstraint[BaseClass1], GenericClassConstraint[TC])
        assert not can_substitute(GenericClassConstraint[DerivedClass1], GenericClassConstraint[TC])
        assert not can_substitute(GenericClassConstraint[TC], GenericClassConstraint[DerivedClass1])
        assert can_substitute(GenericClassConstraint[BaseClass1], GenericClassConstraint)
        assert not can_substitute(GenericClassConstraint[DerivedClass1], GenericClassConstraint)
        assert not can_substitute(GenericClassConstraint, GenericClassConstraint[DerivedClass1])

    def test_can_substitute_to_optional(self):
        assert can_substitute(DerivedClass1, Optional[DerivedClass1])
        assert can_substitute(DerivedClass1, Optional[BaseClass1])
        assert not can_substitute(Optional[DerivedClass1], DerivedClass1)
        assert not can_substitute(Optional[BaseClass1], DerivedClass1)

    def test_can_substitute_to_callable_class(self):
        assert can_substitute(CallableClass, typing.Callable[[str, float], int])

    def test_can_substitute_to_callable_callable(self):
        assert can_substitute(
            typing.Callable[[BaseClass1], BaseClass2],
            typing.Callable[[DerivedClass1], BaseClass2]
        )
        assert not can_substitute(
            typing.Callable[[DerivedClass1], BaseClass2],
            typing.Callable[[BaseClass1], BaseClass2]
        )
        assert can_substitute(
            typing.Callable[[BaseClass1], DerivedClass2],
            typing.Callable[[BaseClass1], BaseClass2]
        )
        assert not can_substitute(
            typing.Callable[[BaseClass1], BaseClass2],
            typing.Callable[[BaseClass1], DerivedClass2]
        )
        assert can_substitute(
            typing.Callable[[BaseClass1], DerivedClass2],
            typing.Callable[[DerivedClass1], BaseClass2]
        )
        assert not can_substitute(
            typing.Callable[[DerivedClass1], BaseClass2],
            typing.Callable[[BaseClass1], DerivedClass2]
        )

    def test_is_weak_overload_of_callable(self):
        assert is_weak_overload_of(
            typing.Callable[[DerivedClass1], BaseClass2],
            typing.Callable[[BaseClass1], BaseClass2]
        )
        assert not is_weak_overload_of(
            typing.Callable[[BaseClass1], BaseClass2],
            typing.Callable[[DerivedClass1], BaseClass2],
        )
        assert is_weak_overload_of(
            typing.Callable[[BaseClass1], DerivedClass2],
            typing.Callable[[BaseClass1], BaseClass2],
        )
        assert not is_weak_overload_of(
            typing.Callable[[BaseClass1], BaseClass2],
            typing.Callable[[BaseClass1], DerivedClass2],
        )
        assert is_weak_overload_of(
            typing.Callable[[DerivedClass1], BaseClass2],
            typing.Callable[[BaseClass1], DerivedClass2],
        )
        assert not is_weak_overload_of(
            typing.Callable[[BaseClass1], DerivedClass2],
            typing.Callable[[DerivedClass1], BaseClass2],
        )

    def test_advanced_isinstance_to_any(self):
        assert advanced_isinstance("", Any)
        assert advanced_isinstance(str, Any)
        assert advanced_isinstance(None, Any)
        assert advanced_isinstance((DerivedClass1(), DerivedClass2()), Any)

    def test_advanced_isinstance_to_none_optional(self):
        assert advanced_isinstance(None, Optional[str])
        assert advanced_isinstance("", Optional[str])

    def test_advanced_isinstance_to_tuples(self):
        assert advanced_isinstance((DerivedClass1(),), Tuple[BaseClass1])
        assert advanced_isinstance((DerivedClass1(),), tuple)
        assert advanced_isinstance((DerivedClass1(), DerivedClass2()), Tuple[BaseClass1, BaseClass2])
        assert advanced_isinstance((DerivedClass1(), BaseClass2()), Tuple[BaseClass1, BaseClass2])
        assert not advanced_isinstance((BaseClass1(), BaseClass2()), Tuple[DerivedClass1, DerivedClass2])
        assert not advanced_isinstance((BaseClass1(), BaseClass2()), Tuple[DerivedClass1, BaseClass2])

    def test_advanced_isinstance_to_generic_class(self):
        assert advanced_isinstance(GenericClass[int](), GenericClass[T1])
        assert advanced_isinstance(GenericClass[int](), GenericClass)
        assert not advanced_isinstance(GenericClass(), GenericClass[int])
        assert not advanced_isinstance(GenericClass[str](), GenericClass[int])

    def test_advanced_isinstance_to_generic_subclass(self):
        print(type(DerivedGenericClass[str, int]()).__bases__)
        assert advanced_isinstance(DerivedGenericClass[str, int](), GenericClass[int])
        # Python erases type information by default.
        # TODO: Handle @generic_aware classes.
        assert advanced_isinstance(DerivedGenericClass[int, str](), GenericClass[int])

    def test_advanced_isinstance_to_generic_class_bound(self):
        TB = typing.TypeVar("TB", bound=BaseClass1)

        class GenericClassBound(typing.Generic[TB]):
            pass

        assert advanced_isinstance(GenericClassBound[DerivedClass1](), GenericClassBound[TB])
        assert advanced_isinstance(GenericClassBound[DerivedClass1](), GenericClassBound)

    def test_advanced_isinstance_to_generic_class_constraint(self):
        TC = typing.TypeVar("TC", BaseClass1, int)

        class GenericClassConstraint(typing.Generic[TC]):
            pass

        assert advanced_isinstance(GenericClassConstraint[BaseClass1](), GenericClassConstraint[TC])
        # Different from can_substitute due to type erasure!
        assert advanced_isinstance(GenericClassConstraint[DerivedClass1](), GenericClassConstraint[TC])
        assert not advanced_isinstance(GenericClassConstraint[TC](), GenericClassConstraint[DerivedClass1])
        assert advanced_isinstance(GenericClassConstraint[BaseClass1](), GenericClassConstraint)
        # Different from can_substitute due to type erasure!
        assert advanced_isinstance(GenericClassConstraint[DerivedClass1](), GenericClassConstraint)
        assert not advanced_isinstance(GenericClassConstraint(), GenericClassConstraint[DerivedClass1])

    def test_advanced_isinstance_to_optional(self):
        assert advanced_isinstance(DerivedClass1(), Optional[DerivedClass1])
        assert advanced_isinstance(DerivedClass1(), Optional[BaseClass1])

    def test_advanced_isinstance_to_callable_class(self):
        assert advanced_isinstance(CallableClass(), typing.Callable[[str, float], int])

    def test_advanced_isinstance_to_callable_callable(self):
        def _fun1(arg: BaseClass1) -> BaseClass2:
            raise NotImplementedError()

        assert advanced_isinstance(
            _fun1,
            typing.Callable[[DerivedClass1], BaseClass2]
        )

        def _fun2(arg: DerivedClass1) -> BaseClass2:
            raise NotImplementedError()

        assert not advanced_isinstance(
            _fun2,
            typing.Callable[[BaseClass1], BaseClass2]
        )

        def _fun3(arg: BaseClass1) -> DerivedClass2:
            raise NotImplementedError()

        assert advanced_isinstance(
            _fun3,
            typing.Callable[[BaseClass1], BaseClass2]
        )

        def _fun3(arg: BaseClass1) -> BaseClass2:
            raise NotImplementedError()

        assert not advanced_isinstance(
            _fun3,
            typing.Callable[[BaseClass1], DerivedClass2]
        )

        def _fun4(arg: BaseClass1) -> DerivedClass2:
            raise NotImplementedError()

        assert advanced_isinstance(
            _fun4,
            typing.Callable[[DerivedClass1], BaseClass2]
        )

        def _fun5(arg: DerivedClass1) -> BaseClass2:
            raise NotImplementedError()

        assert not advanced_isinstance(
            _fun5,
            typing.Callable[[BaseClass1], DerivedClass2]
        )
