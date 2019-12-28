import gc
import weakref
from abc import ABC, abstractmethod
from typing import Tuple, Optional

import pytest

from grundzeug.container.impl import Container
from grundzeug.container.di import injectable, inject, Inject
from grundzeug.container.registrations import TransientFactoryContainerRegistration, \
    HierarchicalFactoryContainerRegistration


class IBean(ABC):
    @property
    @abstractmethod
    def foo(self):
        raise NotImplementedError()


class Bean(IBean):
    @property
    def foo(self):
        return "bar"


class Bean2(IBean):
    @property
    def foo(self):
        return "baz"


@injectable
class SecondBeanType:
    bean: Inject[IBean]

    def __init__(self, arg: int, kwarg: str):
        self.kwarg = kwarg
        self.arg = arg


@injectable
class SecondBeanField:
    bean: IBean = inject[IBean]

    def __init__(self, arg: int, kwarg: str):
        self.kwarg = kwarg
        self.arg = arg


def injectable_func_type(
        arg: int,
        kwarg: str,
        bean: Inject[IBean]
) -> Tuple[int, str, IBean]:
    return arg, kwarg, bean


def injectable_func_field(
        arg: int,
        kwarg: str,
        bean: IBean = inject[IBean]()
) -> Tuple[int, str, IBean]:
    return arg, kwarg, bean


injectable_func_parametrize = pytest.mark.parametrize(
    "func",
    [
        injectable_func_type,
        injectable_func_field
    ],
)


class TestDI:
    @injectable_func_parametrize
    def test_func_instance_injection(self, func):
        container = Container()
        bean = Bean()
        container.register_instance[IBean](bean)
        x, y, z = container.inject_func(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert z == bean
        assert z.foo == "bar"

    @injectable_func_parametrize
    def test_func_factory_injection(self, func):
        container = Container()
        container.register_factory[IBean](lambda: Bean())
        x, y, z = container.inject_func(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert isinstance(z, Bean)
        assert z.foo == "bar"

    @injectable_func_parametrize
    def test_func_type_injection(self, func):
        container = Container()
        container.register_type[IBean, Bean]()
        x, y, z = container.inject_func(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert isinstance(z, Bean)
        assert z.foo == "bar"

    @injectable_func_parametrize
    def test_func_factory_injection_transient(self, func):
        container = Container()
        container.register_factory[IBean](
            lambda: Bean(),
            registration_type=TransientFactoryContainerRegistration
        )
        x1, y1, z1 = container.inject_func(func)(42, kwarg="baz")
        x2, y2, z2 = container.inject_func(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(z1, Bean)
        assert z1.foo == "bar"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(z2, Bean)
        assert z2.foo == "bar"
        assert z1 != z2

    @injectable_func_parametrize
    def test_func_factory_injection_container_controlled(self, func):
        container = Container()
        container.register_factory[IBean](lambda: Bean())
        child_container = Container(container)
        x1, y1, z1 = container.inject_func(func)(42, kwarg="baz")
        x2, y2, z2 = child_container.inject_func(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(z1, Bean)
        assert z1.foo == "bar"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(z2, Bean)
        assert z2.foo == "bar"
        assert z1 == z2

    @injectable_func_parametrize
    def test_func_factory_injection_hierarchical(self, func):
        container = Container()
        container.register_factory[IBean](
            lambda: Bean(),
            registration_type=HierarchicalFactoryContainerRegistration
        )
        child_container = Container(container)
        x1, y1, z1 = container.inject_func(func)(42, kwarg="baz")
        x2, y2, z2 = child_container.inject_func(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(z1, Bean)
        assert z1.foo == "bar"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(z2, Bean)
        assert z2.foo == "bar"
        assert z1 != z2

    @pytest.mark.parametrize(
        "clazz",
        [
            SecondBeanType,
            SecondBeanField
        ],
    )
    def test_field_injection(self, clazz):
        container = Container()
        container.register_factory[IBean](lambda: Bean())
        second_bean = container.inject_func(clazz)(42, kwarg="baz")
        assert second_bean.arg == 42
        assert second_bean.kwarg == "baz"
        assert isinstance(second_bean.bean, Bean)
        assert second_bean.bean.foo == "bar"

    @injectable_func_parametrize
    def test_func_instance_injection_finalizer_called(self, func):
        container = Container()
        container2 = Container(container)

        bean_removed = False
        plugin_storage_removed = False
        container2_removed = False

        class _Bean():
            def __del__(self):
                nonlocal bean_removed
                bean_removed = True

        bean = _Bean()

        def mark_bean_removed():
            nonlocal plugin_storage_removed
            plugin_storage_removed = True

        def mark_container2_removed():
            nonlocal container2_removed
            container2_removed = True

        weakref.finalize(container2._plugin_storage, mark_bean_removed)
        weakref.finalize(container2, mark_container2_removed)

        container2.register_instance[IBean](bean)
        container2.inject_func(func)(42, kwarg="baz")

        assert bean_removed == False
        assert plugin_storage_removed == False
        assert container2_removed == False
        assert len(container2._plugin_storage) == 1

        del bean
        del container2
        gc.collect()

        assert bean_removed == True
        assert plugin_storage_removed == True
        assert container2_removed == True
