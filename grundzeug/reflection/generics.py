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
import typing
from typing import TypeVar, Dict, Union, _GenericAlias, List

from grundzeug.util.collections import zip_equal
from grundzeug.util.sentinels import make_sentinel


def _generic_aware_impl_wrap_classmethod(class_member, specialized_class, supplemental_dict, name):
    func = getattr(class_member, "__func__")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(specialized_class, *args, **kwargs)

    supplemental_dict[name] = wrapper


_extra_field_dict = "__grundzeug_extradict__"


# Pure evil: monkey-patch typing._GenericAlias to support class-specific attributes.
# This is done because we can't modify __get_attr__ on instances of typing._GenericAlias and we can't subclass
# typing._GenericAlias directly.
def _patch_generic_alias():
    orig_getattr = typing._GenericAlias.__getattr__

    @functools.wraps(orig_getattr)
    def wrapped___getattr__(cls, attr):
        extra_dict = cls.__dict__.get(_extra_field_dict, {})
        if attr in extra_dict:
            v = extra_dict[attr]
            if hasattr(v, "__get__"):
                return v.__get__(None, cls)
            return v
        return orig_getattr(cls, attr)

    typing._GenericAlias.__getattr__ = wrapped___getattr__

    orig_setattr = typing._GenericAlias.__setattr__

    @functools.wraps(orig_getattr)
    def wrapped___setattr__(cls, attr, value):
        extra_dict = cls.__dict__.get(_extra_field_dict, {})
        if attr in extra_dict:
            v = extra_dict[attr]
            if hasattr(v, "__set__"):
                v.__set__(None, value)
                return
            extra_dict[attr] = v
        return orig_setattr(cls, attr, value)

    typing._GenericAlias.__setattr__ = wrapped___setattr__


_patch_generic_alias()


def specialize_class(specialized_class, process_default_classmethod: bool = True):
    """
    Update the class by overriding all fields set to instances of
    :py:class:`~grundzeug.reflection.generics.generic_accessor` and methods decorated with
    :py:func:`~grundzeug.reflection.generics.generic_classmethod` or ``@classmethod`` (if
    ``process_default_classmethod`` is set to ``True``).

    :param specialized_class: The specialized class to update, as returned by \
                              :py:meth:`~typing.Generic.__class_getitem__`.
    :param process_default_classmethod: If set to ``False``, only methods decorated with \
                                        :py:func:`~grundzeug.reflection.generics.generic_classmethod` \
                                        will receive specialized classes as arguments instead of the generic class. If \
                                        set to ``True``, methods decorated with ``@classmethod`` will act like methods \
                                        annotated with :py:func:`~grundzeug.reflection.generics.generic_classmethod`.
    """
    supplemental_dict = {}
    for name, class_member in specialized_class.__origin__.__dict__.items():
        if isinstance(class_member, generic_classmethod) or \
                (process_default_classmethod and isinstance(class_member, classmethod)):
            _generic_aware_impl_wrap_classmethod(class_member, specialized_class, supplemental_dict, name)
        if isinstance(class_member, generic_accessor):
            supplemental_dict[name] = generic_accessor(class_member.type_var, _class_override=specialized_class)
    specialized_class.__dict__[_extra_field_dict] = supplemental_dict


def _generic_aware_impl(cls: type, process_default_classmethod: bool = True):
    orig__class_getitem__ = cls.__class_getitem__

    @functools.wraps(orig__class_getitem__)
    def __class_getitem__(cls):
        specialized_class = orig__class_getitem__(cls)
        specialize_class(specialized_class, process_default_classmethod=process_default_classmethod)
        return specialized_class

    cls.__class_getitem__ = __class_getitem__

    return cls


def generic_aware(cls=None, *, process_default_classmethod: bool = True):
    """
    Makes :py:func:`~grundzeug.reflection.generics.generic_accessor` and
    :py:func:`~grundzeug.reflection.generics.generic_classmethod` work inside the decorated class.

    If ``process_default_classmethod`` is set to ``True``, methods annotated with ``@classmethod`` are also going to
    receive a specialized class instead of the generic class as an argument.



    :param cls: The class to decorate.
    :param process_default_classmethod: If set to ``False``, only methods decorated with \
                                        :py:func:`~grundzeug.reflection.generics.generic_classmethod` \
                                        will receive specialized classes as arguments instead of the generic class. If \
                                        set to ``True``, methods decorated with ``@classmethod`` will act like methods \
                                        annotated with :py:func:`~grundzeug.reflection.generics.generic_classmethod`.
    """

    def wrap(cls):
        return _generic_aware_impl(cls, process_default_classmethod=process_default_classmethod)

    if cls is None:
        return wrap
    return wrap(cls)


_, _generic_class_override_sentinel = make_sentinel()


class generic_accessor():
    """
    A field descriptor that specifies that this field should contain the value of the specified type variable.
    The parent class must be :py:func:`~grundzeug.reflection.generics.generic_aware`.

    Usage:

    .. code-block:: python

        T = TypeVar("T")
        @generic_aware
        class GenericClass(Generic[T]):
            generic_T = generic_accessor(T)

        assert GenericClass[str].generic_T == str

    """

    def __init__(self, type_var: TypeVar, *, _class_override=_generic_class_override_sentinel):
        """
        :param type_var:
        """
        self.type_var = type_var
        self.__class_override = _class_override

    def __get__(self, obj, klass=None):
        klass = self._get_class(klass, obj)
        return get_type_arguments(klass)[self.type_var]

    def _get_class(self, klass, obj):
        if self.__class_override is _generic_class_override_sentinel:
            if klass is None:
                return type(obj)
            return klass
        return self.__class_override


class generic_classmethod(object):
    """
    A substitute for ``classmethod`` that can be used to distinguish classmethods that should receive the generic \
    alias from those that should simply receive the generic class.
    """

    def __init__(self, f):
        self.__func__ = f

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)

        @functools.wraps(self.__func__)
        def wrapper(*args):
            return self.__func__(klass, *args)

        return wrapper


def get_type_parameters(cls: type) -> List[TypeVar]:
    """
    :param cls: a generic class or a generic alias.
    :return: a list of type parameters of the generic class.
    """
    if isinstance(cls, _GenericAlias):
        return get_type_parameters(cls.__origin__)

    return cls.__parameters__


def get_type_arguments(cls: type) -> Dict[TypeVar, Union[TypeVar, typing.Any]]:
    """
    :param cls: a generic alias of a generic class.
    :return: a dictionary mapping the type parameters of the generic class to the type arguments specified in the \
             generic alias.
    """
    if not isinstance(cls, _GenericAlias):
        return {
            type_var: type_var
            for type_var
            in get_type_parameters(cls)
        }

    return {
        type_var: type_var_value
        for type_var, type_var_value
        in zip_equal(get_type_parameters(cls), getattr(cls, "__args__", ()))
    }


__all__ = ["generic_aware", "generic_accessor", "generic_classmethod", "get_type_arguments", "get_type_parameters"]
