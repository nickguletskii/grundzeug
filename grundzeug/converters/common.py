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
from abc import abstractmethod, ABC
from grundzeug.reflection.generics import generic_aware, get_type_arguments, generic_accessor
from grundzeug.reflection.types import can_substitute

TFrom = typing.TypeVar("TFrom")
TTo = typing.TypeVar("TTo")


@generic_aware
class Converter(typing.Generic[TFrom, TTo], ABC):
    """
    A base class/protocol for callables that perform the conversion of values from type ``TFrom`` to type ``TTo``.
    """
    generic_TFrom = generic_accessor(TFrom)
    generic_TTo = generic_accessor(TTo)

    @abstractmethod
    def __call__(self, value: TFrom) -> TTo:
        """
        Performs the conversion from ``TFrom`` to ``TTo``.

        :param value: A value of type ``TFrom`` to be converted into ``TTo``.
        :return: The converted value.
        """
        raise NotImplementedError()

    @classmethod
    def identity(cls) -> "Converter[TFrom, TTo]":
        """
        :return: An identity converter that maps ``x`` to ``x``.
        :raises ValueError: If ``type_from`` or ``type_to`` is a :py:class:`~typing.TypeVar`.
        :raises ValueError: If ``type_from`` can't substitute ``type_to`` according to the Liskov Substitution \
                            Principle. More specifically, a ``ValueError`` is raised if \
                            ``not can_substitute(type_from, type_to)``. See \
                            :py:func:`~grundzeug.reflection.types.can_substitute` for more details.
        """
        type_args = get_type_arguments(cls)
        type_from = type_args[TFrom]
        type_to = type_args[TTo]
        if isinstance(type_to, typing.TypeVar) or isinstance(type_from, typing.TypeVar):
            raise ValueError(f"Attempt to call 'identity' on a generic Converter class. Please provide concrete type "
                             f"arguments to resolve this error.")
        if not can_substitute(type_from, type_to):
            raise ValueError(f"TFrom={type_from} must be a subclass of TTo={type_to} for an identity mapping to exist "
                             f"from TFrom to TTo.")

        class _IdentityConverter(cls):
            def __call__(self, value: TFrom) -> TTo:
                return value

        return _IdentityConverter()

    @classmethod
    def cast(cls) -> "Converter[TFrom, TTo]":
        """
        :return: A converter that maps ``x`` to ``TTo(x)``. For instance, if ``TTo`` is ``str``, then ``x`` will be \
                 mapped to ``str(x)``.
        :raises ValueError: If ``type_to`` is a :py:class:`~typing.TypeVar`.
        """
        type_args = get_type_arguments(cls)

        type_to = type_args[TTo]
        if isinstance(type_to, typing.TypeVar):
            raise ValueError(f"Attempt to call 'cast' on a generic Converter class. Please provide a concrete type for "
                             f"TTo to resolve this error.")

        class _CastConverter(cls):
            def __call__(self, value: TFrom) -> TTo:
                return type_to(value)

        return _CastConverter()


__all__ = ["Converter"]
