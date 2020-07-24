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
import collections
import inspect
import typing
from typing import _GenericAlias


def is_generic_alias_of(to_check, type_def):
    """
    :param to_check: the type that is supposed to be a generic alias of ``type_def`` if this function returns ``True``.
    :param type_def: the type that is supposed to be a generic version of ``to_check`` if this function returns \
                     ``True``.
    :return: ``True`` if ``to_check`` is a generic alias of ``type_def``, ``False`` otherwise.
    """
    if isinstance(to_check, type) and issubclass(to_check, type_def):
        return True
    origin = getattr(to_check, "__origin__", None)
    if origin is not None:
        return issubclass(origin, type_def)
    return False


def is_none_type(to_check):
    """
    :param to_check: the type to check.
    :return: ``True`` if ``to_check`` is either ``NoneType`` or ``None`` (acceptable alias of ``NoneType``).
    """
    if to_check is None:
        return True
    if to_check is type(None):
        return True
    return False


def is_any_type(type_def) -> bool:
    """
    Checks whether the specified type definition accepts any type.

    :param type_def: the type to check.
    :return: ``True`` if ``type_def`` is :py:data:`~typing.Any` or ``Union[T_1, ..., T_N]`` where there exists some i, \
             for which ``is_any_type(T_i)`` is ``True``; ``False`` otherwise.
    """
    if type_def is typing.Any:
        return True

    if isinstance(type_def, _GenericAlias) and type_def.__origin__ == typing.Union:
        return any(is_any_type(x) for x in type_def.__args__)

    return False


def extract_callable_parameters_and_return_type(callable) -> typing.Tuple[typing.Tuple[typing.Any, ...], typing.Any]:
    """
    :param callable: the callable to extract the parameters and the return type from. May be a function, \
                     :py:class:`typing.Callable`, or a callable class.
    :return: a tuple consisting of two elements: a tuple of parameter types of the callable and the callable's return \
             type.
    """
    if isinstance(callable, _GenericAlias) and \
            (callable.__origin__ == typing.Callable or callable.__origin__ == collections.abc.Callable):
        return callable.__args__[:-1], callable.__args__[-1]

    is_function = isinstance(callable, type(_check_callable_signature))
    signature: inspect.Signature = inspect.signature(callable if is_function else callable.__call__)
    params = [x.annotation for x in signature.parameters.values()]
    if not is_function and can_substitute(type(callable), type):
        # If callable is an object, the first argument is self
        params = params[1:]
    return tuple(params), signature.return_annotation


def _check_callable_signature(to_check, type_def, check_more_specific):
    if not is_callable(to_check, allow_callable_class=True):
        return False
    to_check_args, to_check_ret = extract_callable_parameters_and_return_type(to_check)
    type_def_args, type_def_ret = extract_callable_parameters_and_return_type(type_def)
    if check_more_specific:
        if _check_tuple_args_compatibility(to_check_args, type_def_args):
            if tuple(to_check_args) != tuple(type_def_args):
                return True
            return can_substitute(to_check_ret, type_def_ret)
        else:
            return False

    return _check_tuple_args_compatibility(type_def_args, to_check_args) \
           and can_substitute(to_check_ret, type_def_ret)


def is_callable(type_def, allow_callable_class: bool = False) -> bool:
    """
    Checks whether the ``type_def`` is a callable according to the following rules:

    1. Functions are callable.
    2. ``typing.Callable`` types are callable.
    3. Generic aliases of types which are ``is_callable`` are callable.
    4. If ``allow_callable_class`` is set to ``True``, then classes which have a ``__call__`` method are callable.

    :param type_def: the type to check.
    :param allow_callable_class: set to ``True`` to consider classes which have a ``__call__``  method callable.
    :return: ``True`` if ``type_def`` is a callable type, ``False`` otherwise.
    """
    if isinstance(type_def, type(_check_callable_signature)):
        return True
    if isinstance(type_def, typing._SpecialForm):
        return False
    if isinstance(type_def, _GenericAlias):
        if type_def.__origin__ == typing.Callable or type_def.__origin__ == collections.abc.Callable:
            return True
        if type_def._special:
            return False
        return is_callable(type_def.__origin__, allow_callable_class=allow_callable_class)
    if allow_callable_class and hasattr(type_def, "__call__"):
        return True
    return False


def can_substitute(to_check, type_def, assume_cant_substitute=False) -> bool:
    """
    Checks whether ``to_check`` can substitute ``type_def`` according to the Liskov Substitution Principle.

    The check is performed by sequentially following the following rules:

    1. If ``type_def`` is ``NoneType``, return ``True`` iff ``to_check`` is ``NoneType``.
    2. If ``type_def`` is :py:data:`~typing.Any`, return ``True``.
    3. If ``to_check`` is :py:data:`~typing.Any`, return ``True`` iff ``type_def`` is :py:data:`~typing.Any` or \
       ``Optional[Any]``.
    4. If ``type_def`` is ``Union[T_1, ..., T_N]`` and ``to_check`` is ``Union[S_1, ..., S_M]``, return ``True`` \
       iff for all ``1<=j<=M`` there exists ``1<=i<=N``  such that ``can_substitute(S_j, T_i)`` is ``True``.
    5. If ``type_def`` is ``Union[T_1, ..., T_N]`` and ``to_check`` is not a ``Union``, return \
       ``can_substitute(Union[to_check], type_def)``.
    6. ``Optional[T]`` is equivalent to ``Union[T, NoneType]`` for all arguments.
    7. If ``type_def`` is ``Tuple[T_1, ..., T_N]``, return ``True`` iff ``to_check`` is ``Tuple[S_1, ..., S_N]`` such \
       that ``can_substitute(S_i, T_i)`` for all i.
    8. If ``type_def`` is ``Callable[[T_1, ..., T_N], TR]``, return ``True`` iff ``to_check`` is a callable with a \
       signature compatible with ``type_def``.
    9. If ``type_def`` is a generic alias of ``T``, and ``to_check`` is not a generic alias, return ``True`` iff all\
       arguments of ``type_def`` are type variables and ``can_substitute(to_check, T)``.
    10. If ``type_def`` is a generic alias of ``T``, and `to_check`` is a generic alias of ``S``, check that \
        ``can_substitute(S, T)`` and  ensure that all type arguments for ``T`` match the corresponding type arguments \
        for ``S``.
    11. If ``to_check`` is ``Union[S_1, ..., S_M]``, return ``True`` iff ``can_substitute(S_i, type_def)`` is ``True`` \
        for all i.
    12. If ``to_check`` is ``Tuple[S_1, ..., S_N]`` and ``type_def`` is not a generic alias, return \
        ``can_substitute(tuple, type_def)``.
    13. If ``to_check`` is ``Callable[[T_1, ..., T_N], TR]``, return ``True`` iff ``type_def`` is a callable  such \
        that ``to_check`` is compatible with the signature of ``type_def``.
    14. If ``to_check`` is a generic alias and ``type_def`` has an attribute called ``__parameters__`` (e.g. if it \
        derives from :py:class:`~typing.Generic`), return ``can_substitute(to_check, type_def[__parameters__])``.
    15. If ``to_check`` is a generic alias of ``S``, return ``can_substitute(S, type_def)``.
    16. If ``to_check`` is ``NoneType``, return ``False``.
    17. If ``to_check`` is a covariant or a contravariant :py:class:`~typing.TypeVar`, raise a \
        :py:class:`~NotImplementedError`.
    18. If ``to_check`` is a :py:class:`~typing.TypeVar` with constraints ``S_1, ..., S_N``, return ``True`` iff \
        ``can_substitute(S_i, type_def)`` for all i.
    19. If ``to_check`` is a :py:class:`~typing.TypeVar` with bound ``S``, return ``True`` iff \
        ``can_substitute(S, type_def)``.
    20. If ``to_check`` is a :py:class:`~typing.TypeVar`, return ``True`` iff ``to_check is type_def``.
    21. If ``to_check`` is a class , return ``issubclass(to_check, type_def)``.
    22. Raise :py:class:`~ValueError`.

    A type definition is determined to be a callable if calling :py:func:`~is_callable` with \
    ``allow_callable_class == True`` returns ``True``.

    A callable's signature is obtained using \
    :py:func:`~grundzeug.reflection.types.extract_callable_parameters_and_return_type`.

    A callable ``to_check`` is considered to be a valid substitution for ``type_def`` iff its parameters are less \
    specific than those of ``type_def`` and its return type is more specific than ``type_def``'s.

    :param to_check: the type that should be able to substitute ``type_def`` if this function returns ``True``.
    :param type_def: the type that should be substitutable by ``to_check`` if this function returns ``True``.
    :param assume_cant_substitute: if ``True``, this function will return ``False`` instead of throwing a \
                                   ``ValueError`` for arguments which can't be compared.
    :return: ``True`` if ``to_check`` can substitute ``type_def``, ``False`` otherwise.
    :raises ValueError: if the arguments are not supported and ``assume_cant_substitute`` is ``False``.
    :raises NotImplementedError: if ``type_def`` is a covariant or a contravariant :py:class:`~typing.TypeVar`.
    """
    return _can_substitute_impl(to_check, type_def, False, assume_cant_substitute)


def is_weak_overload_of(to_check, type_def, assume_cant_substitute=False):
    """
    Checks whether ``to_check`` is at least as specific as ``type_def``.

    Behaves like :py:func:`~grundzeug.reflection.types.can_substitute`, except for callables and unions of callables,
    which are treated as follows:

    1. If ``to_check`` has a tuple of parameters that can substitute the parameters of ``type_def`` and the tuples of \
       parameters for ``to_check`` and ``type_def`` differ, return ``True``.
    2. If ``to_check`` has a tuple of parameters that can substitute the parameters of ``type_def`` and the tuples of \
       parameters for ``to_check`` and ``type_def`` are equal, return ``True`` iff the return type of ``to_check`` can \
       substitute the return type of ``type_def``.


    :param to_check: the type that should be at least as specific as ``type_def`` if this function returns ``True``.
    :param type_def: the type that should be at most as specific as ``to_check`` if this function returns ``True``.
    :param assume_cant_substitute: if ``True``, this function will return ``False`` instead of throwing a \
                                   ``ValueError`` for arguments which can't be compared.
    :return: ``True`` if ``to_check`` is at least as specific as ``type_def``, ``False`` otherwise.
    :raises ValueError: if the arguments are not supported and ``assume_cant_substitute`` is ``False``.
    """

    return _can_substitute_impl(to_check, type_def, True, assume_cant_substitute)


def _can_substitute_impl(to_check, type_def, check_is_weak_overload_of, assume_cant_substitute):
    if is_none_type(type_def):
        return is_none_type(to_check)

    if is_any_type(type_def):
        return True

    if is_any_type(to_check):
        return False

    if isinstance(type_def, typing.TypeVar):
        if type_def.__covariant__ or type_def.__contravariant__:
            raise NotImplementedError(f"TypeVar covariance and contravariance is currently not supported.")
        if len(type_def.__constraints__) > 0:
            return any(to_check == x for x in type_def.__constraints__)
        if type_def.__bound__ is not None:
            return _can_substitute_impl(to_check, type_def.__bound__, check_is_weak_overload_of, assume_cant_substitute)
        return True

    if isinstance(type_def, _GenericAlias):
        if type_def.__origin__ == typing.Union:
            # Handles both Union and Optional
            return _is_assignable_union(to_check, type_def)
        elif type_def.__origin__ == tuple:
            if not isinstance(to_check, _GenericAlias):
                return False
            args_def = type_def.__args__
            args_to_check = to_check.__args__
            return _check_tuple_args_compatibility(args_to_check, args_def)
        elif type_def.__origin__ == typing.Callable or type_def.__origin__ == collections.abc.Callable:
            return _check_callable_signature(to_check, type_def, check_is_weak_overload_of)
        else:
            if not isinstance(to_check, _GenericAlias):
                if all(isinstance(x, typing.TypeVar) for x in type_def.__args__):
                    # Generic class origin is assignable to its non-specialized generic wrapper
                    return can_substitute(to_check, type_def.__origin__)
                return False
            if not can_substitute(to_check.__origin__, type_def.__origin__):
                return False
            args1 = {k: v for k, v in zip(to_check.__origin__.__parameters__, to_check.__args__)}
            for k, v in zip(type_def.__origin__.__parameters__, type_def.__args__):
                if not can_substitute(args1[k], v):
                    return False
            return True

    if isinstance(to_check, _GenericAlias):
        if to_check.__origin__ == typing.Union:
            # Handles both Union and Optional
            return all(can_substitute(x, type_def) for x in to_check.__args__)
        elif to_check.__origin__ == tuple:
            return can_substitute(tuple, type_def)
        elif to_check.__origin__ == typing.Callable or to_check.__origin__ == collections.abc.Callable:
            return _check_callable_signature(to_check, type_def, check_is_weak_overload_of)
        elif hasattr(type_def, "__parameters__"):
            return _can_substitute_impl(to_check, type_def[type_def.__parameters__], check_is_weak_overload_of,
                                        assume_cant_substitute)
        # The type def is not a generic alias, so it may be a non-generic version of the class
        return can_substitute(to_check.__origin__, type_def)

    if is_none_type(to_check):
        return False

    if isinstance(to_check, typing.TypeVar):
        if to_check.__covariant__ or to_check.__contravariant__:
            raise NotImplementedError(f"TypeVar covariance and contravariance is currently not supported.")
        if len(to_check.__constraints__) > 0:
            return all(
                _can_substitute_impl(x, type_def, check_is_weak_overload_of, assume_cant_substitute)
                for x
                in to_check.__constraints__
            )
        if to_check.__bound__ is not None:
            return _can_substitute_impl(to_check.__bound__, type_def, check_is_weak_overload_of, assume_cant_substitute)
        return to_check is type_def

    if inspect.isclass(to_check):
        return issubclass(to_check, type_def)

    if assume_cant_substitute:
        return False

    raise ValueError(f"Unsupported arguments: {to_check}, {type_def}")


def _is_assignable_union(to_check, type_def):
    if isinstance(to_check, _GenericAlias) and to_check.__origin__ == typing.Union:
        # Handle situation when both type definitions are Unions
        return all(any(can_substitute(y, x) for x in type_def.__args__) for y in to_check.__args__)
    return any(can_substitute(to_check, x) for x in type_def.__args__)


def _check_tuple_args_compatibility(
        args_def: typing.Sequence[typing.Any],
        args_to_check: typing.Sequence[typing.Any]
) -> bool:
    if len(args_def) == 2 and args_def[1] is Ellipsis:
        if len(args_to_check) == 2 and args_to_check[1] is Ellipsis:
            # Tuple[x, ...] is assignable to Tuple[y, ...] iff x is assignable to y
            return can_substitute(args_to_check[0], args_def[0])
        # Tuple[x1, x2,,, xn] is assignable to Tuple[y, ...] iff x1, ..., xn are all assignable to y
        return all(can_substitute(x, args_def[0]) for x in args_to_check)
    # Tuple[x, ...] is not assignable to Tuple[y1, y2,,, yn]
    if len(args_to_check) == 2 and args_to_check[1] is Ellipsis:
        return False
    # Tuple[x1, x2,,, xn] is assignable to Tuple[y1, y2,,, yn] iff xi is assignable to yi for all i.
    return len(args_def) == len(args_to_check) \
           and all(can_substitute(x, y) for x, y in zip(args_def, args_to_check))


def advanced_isinstance(instance, type_def) -> bool:
    """
    An improved version of python's ``isinstance`` that takes care of unions, tuples, generic type definitions and other
    types that can be handled using :py:func:`~grundzeug.reflection.types.can_substitute`.

    1. If ``type_def`` is a union, checks if ``instance`` is an ``advanced_isinstance`` of any element of the union.
    2. If ``type_def`` is a tuple definition, checks if ``instance`` is a tuple that matches the signature specified \
       in ``type_def``.
    3. If ``type_def`` is a callable, checks if ``instance`` is a callable with a signature that satisfies the \
       constraint.
    4. If ``type_def`` is a generic class definition and the type of ``instance`` can substitute ``type_def`` \
       according to :py:func:`~grundzeug.reflection.types.can_substitute`, return ``True``.
    5. If ``type_def`` is a generic class definition and any base class of ``instance`` can substitute ``type_def`` \
       according to :py:func:`~grundzeug.reflection.types.can_substitute`, return ``True``.
    6. Otherwise, if ``type_def`` is a generic class definition, return ``False``.

    For all other types, ``can_substitute(type(instance), type_def)`` is returned.

    :param instance: The instance to check against ``type_def``.
    :param type_def: The type definition that should include ``instance`` if this function returns ``True``.
    :return: ``True`` if ``instance`` satisfies the type constraint ``type_def``, ``False`` otherwise.
    """
    if isinstance(type_def, _GenericAlias):
        if type_def.__origin__ == typing.Union:
            # Handles both Union and Optional
            return any(advanced_isinstance(instance, x) for x in type_def.__args__)
        elif type_def.__origin__ == tuple:
            args_def = type_def.__args__
            if not can_substitute(type(instance), tuple):
                return False
            return _check_tuple_args_compatibility(tuple(type(x) for x in instance), args_def)
        elif type_def.__origin__ == typing.Callable or type_def.__origin__ == collections.abc.Callable:
            return _check_callable_signature(instance, type_def, False)
        else:
            if can_substitute(type(instance), type_def):
                return True
            # When a class inherits a generic class, its type information is erased for some reason.
            # TODO: Check what can be done about this. Maybe @generic_aware classes should be handled differently?
            for base in type(instance).__bases__:
                if can_substitute(base, type_def.__origin__):
                    return True
            return False

    return can_substitute(type(instance), type_def)


__all__ = ["is_generic_alias_of", "is_none_type", "is_any_type", "extract_callable_parameters_and_return_type",
           "is_callable", "can_substitute", "is_weak_overload_of", "advanced_isinstance"]
