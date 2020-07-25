import gc
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

import pytest
from typing_extensions import Annotated

from grundzeug.container.di import injectable, inject_value, Inject, InjectNamed
from grundzeug.container.impl import Container
from grundzeug.container.registrations import TransientFactoryContainerRegistration, \
    HierarchicalFactoryContainerRegistration


class IBean(ABC):
    @property
    @abstractmethod
    def foo(self):
        raise NotImplementedError()


class Bean(IBean):
    def __init__(self, name: str):
        self.name = name

    @property
    def foo(self):
        return f"bar_{self.name}"


class UnnamedBean(Bean):
    def __init__(self):
        super().__init__("unnamed_bean")


class NamedBean(Bean):
    def __init__(self):
        super().__init__("named_bean")


class Bean2(IBean):
    @property
    def foo(self):
        return "baz"


@injectable
class SecondBeanType:
    unnamed_bean: Inject[IBean]
    named_bean: InjectNamed[IBean, "named_bean"]

    def __init__(self, arg: int, kwarg: str):
        self.kwarg = kwarg
        self.arg = arg


@dataclass
class DataclassSecondBeanType:
    unnamed_bean: Inject[IBean]
    named_bean: InjectNamed[IBean, "named_bean"]


@injectable
class SecondBeanField:
    unnamed_bean: IBean = inject_value[IBean]
    named_bean: IBean = inject_value[IBean].named("named_bean")

    def __init__(self, arg: int, kwarg: str):
        self.kwarg = kwarg
        self.arg = arg


def injectable_func_type(
        arg: int,
        kwarg: str,
        bean: Inject[IBean],
        named_bean: InjectNamed[IBean, "named_bean"]
) -> Tuple[int, str, IBean, IBean]:
    return arg, kwarg, bean, named_bean


def injectable_func_field(
        arg: int,
        kwarg: str,
        bean: IBean = inject_value[IBean](),
        named_bean: IBean = inject_value[IBean](bean_name="named_bean")
) -> Tuple[int, str, IBean, IBean]:
    return arg, kwarg, bean, named_bean


injectable_func_parametrize = pytest.mark.parametrize(
    "func",
    [
        injectable_func_type,
        injectable_func_field
    ],
)


class TestDI:
    @injectable_func_parametrize
    def test_func_get_kwargs_to_inject(self, func):
        container = Container()
        bean1 = Bean("unnamed_bean")
        bean2 = Bean("named_bean")
        container.register_instance[IBean](bean1)
        container.register_instance[IBean](bean2, bean_name="named_bean")
        kwargs = container.get_kwargs_to_inject(func)
        assert kwargs == {
            "bean": bean1,
            "named_bean": bean2
        }

    @injectable_func_parametrize
    def test_func_instance_injection(self, func):
        container = Container()
        bean = Bean("unnamed_bean")
        container.register_instance[IBean](bean)
        named_bean = Bean("named_bean")
        container.register_instance[IBean](named_bean, bean_name="named_bean")
        x, y, unnamed_bean_received, named_bean_received = container.inject(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert unnamed_bean_received == bean
        assert unnamed_bean_received.foo == "bar_unnamed_bean"
        assert named_bean_received == named_bean
        assert named_bean_received.foo == "bar_named_bean"

    @injectable_func_parametrize
    def test_func_factory_injection(self, func):
        container = Container()
        container.register_factory[IBean](lambda: Bean("unnamed_bean"))
        container.register_factory[IBean](lambda: Bean("named_bean"), bean_name="named_bean")
        x, y, unnamed_bean_received, named_bean_received = container.inject(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert isinstance(unnamed_bean_received, Bean)
        assert unnamed_bean_received.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received, Bean)
        assert named_bean_received.foo == "bar_named_bean"

    @injectable_func_parametrize
    def test_func_type_injection(self, func):
        container = Container()
        container.register_type[IBean, UnnamedBean]()
        container.register_type[IBean, NamedBean](bean_name="named_bean")
        x, y, unnamed_bean_received, named_bean_received = container.inject(func)(42, kwarg="baz")
        assert x == 42
        assert y == "baz"
        assert isinstance(unnamed_bean_received, Bean)
        assert unnamed_bean_received.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received, Bean)
        assert named_bean_received.foo == "bar_named_bean"

    @injectable_func_parametrize
    def test_func_factory_injection_transient(self, func):
        container = Container()
        container.register_factory[IBean](
            lambda: Bean("unnamed_bean"),
            registration_type=TransientFactoryContainerRegistration
        )
        container.register_factory[IBean](
            lambda: Bean("named_bean"),
            bean_name="named_bean",
            registration_type=TransientFactoryContainerRegistration
        )
        x1, y1, unnamed_bean_received1, named_bean_received1 = container.inject(func)(42, kwarg="baz")
        x2, y2, unnamed_bean_received2, named_bean_received2 = container.inject(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(unnamed_bean_received1, Bean)
        assert unnamed_bean_received1.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received1, Bean)
        assert named_bean_received1.foo == "bar_named_bean"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(unnamed_bean_received2, Bean)
        assert unnamed_bean_received2.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received2, Bean)
        assert named_bean_received2.foo == "bar_named_bean"
        assert unnamed_bean_received1 != unnamed_bean_received2
        assert named_bean_received1 != named_bean_received2

    @injectable_func_parametrize
    def test_func_factory_injection_container_controlled(self, func):
        container = Container()
        container.register_factory[IBean](lambda: Bean("unnamed_bean"))
        container.register_factory[IBean](lambda: Bean("named_bean"), bean_name="named_bean")
        child_container = Container(container)
        x1, y1, unnamed_bean_received1, named_bean_received1 = container.inject(func)(42, kwarg="baz")
        x2, y2, unnamed_bean_received2, named_bean_received2 = child_container.inject(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(unnamed_bean_received1, Bean)
        assert unnamed_bean_received1.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received1, Bean)
        assert named_bean_received1.foo == "bar_named_bean"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(unnamed_bean_received2, Bean)
        assert unnamed_bean_received2.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received2, Bean)
        assert named_bean_received2.foo == "bar_named_bean"
        assert unnamed_bean_received1 == unnamed_bean_received2
        assert named_bean_received1 == named_bean_received2

    @injectable_func_parametrize
    def test_func_factory_injection_hierarchical(self, func):
        container = Container()
        container.register_factory[IBean](
            lambda: Bean("unnamed_bean"),
            registration_type=HierarchicalFactoryContainerRegistration
        )
        container.register_factory[IBean](
            lambda: Bean("named_bean"),
            bean_name="named_bean",
            registration_type=HierarchicalFactoryContainerRegistration
        )
        child_container = Container(container)
        x1, y1, unnamed_bean_received1, named_bean_received1 = container.inject(func)(42, kwarg="baz")
        x2, y2, unnamed_bean_received2, named_bean_received2 = child_container.inject(func)(42, kwarg="baz")
        assert x1 == 42
        assert y1 == "baz"
        assert isinstance(unnamed_bean_received1, Bean)
        assert unnamed_bean_received1.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received1, Bean)
        assert named_bean_received1.foo == "bar_named_bean"
        assert x2 == 42
        assert y2 == "baz"
        assert isinstance(unnamed_bean_received2, Bean)
        assert unnamed_bean_received2.foo == "bar_unnamed_bean"
        assert isinstance(named_bean_received2, Bean)
        assert named_bean_received2.foo == "bar_named_bean"
        assert unnamed_bean_received1 != unnamed_bean_received2
        assert named_bean_received1 != named_bean_received2

    @pytest.mark.parametrize(
        "clazz",
        [
            SecondBeanType,
            SecondBeanField
        ],
    )
    def test_field_injection(self, clazz):
        container = Container()
        container.register_factory[IBean](lambda: Bean("unnamed_bean"))
        container.register_factory[IBean](lambda: Bean("named_bean"), bean_name="named_bean")
        second_bean = container.inject(clazz)(42, kwarg="baz")
        assert second_bean.arg == 42
        assert second_bean.kwarg == "baz"
        assert isinstance(second_bean.unnamed_bean, Bean)
        assert second_bean.unnamed_bean.foo == "bar_unnamed_bean"
        assert isinstance(second_bean.named_bean, Bean)
        assert second_bean.named_bean.foo == "bar_named_bean"

    def test_field_injection_dataclass(self):
        container = Container()
        container.register_factory[IBean](lambda: Bean("unnamed_bean"))
        container.register_factory[IBean](lambda: Bean("named_bean"), bean_name="named_bean")
        second_bean = container.inject(DataclassSecondBeanType)()
        assert isinstance(second_bean.unnamed_bean, Bean)
        assert second_bean.unnamed_bean.foo == "bar_unnamed_bean"
        assert isinstance(second_bean.named_bean, Bean)
        assert second_bean.named_bean.foo == "bar_named_bean"

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
        container2.register_instance[IBean](bean, bean_name="named_bean")
        container2.inject(func)(42, kwarg="baz")

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

    def test_shortened_type_annotation(self):
        def injectable_func(bean: Annotated[IBean, Inject]):
            return 42

        container = Container()
        container.register_instance[IBean](Bean("test"))
        injected_func = container.inject(injectable_func)
        assert injected_func() == 42
