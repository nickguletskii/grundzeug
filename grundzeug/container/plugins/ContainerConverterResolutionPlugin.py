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

from grundzeug.container import RegistrationKey, IContainer, ContainerRegistration
from grundzeug.container.plugins.ContainerAmbiguousResolutionPluginBase import ContainerAmbiguousResolutionPluginBase
from grundzeug.converters.common import Converter
from grundzeug.reflection.types import can_substitute


class ContainerConverterResolutionPlugin(ContainerAmbiguousResolutionPluginBase):
    """
    Handles ``Converter[TFrom, TTo]`` contracts. Upon resolution, this plugin will attempt to resolve the most specific
    converter that is compatible with the requested ``Converter``. For instance, if we register
    ``Converter[Any, str]`` and ``Converter[BaseClass, str]``, and then request a ``Converter[DerivedClass, str]``,
    this plugin will return the registered ``Converter[BaseClass, str]``.

    Converter compatibility is determined according to the Liskov Substitution Principle and function subtyping. Namely,
    a ``Converter[TFrom1, TTo1]`` is considered to be more specific than ``Converter[TFrom2, TTo2]`` iff
    ``can_substitute(TFrom1, TFrom2) and can_substitute(TTo2, TTo1)``. See
    :py:func:`~grundzeug.reflection.types.can_substitute` for more details.
    """

    def is_registration_key_supported(self, registration_key: RegistrationKey):
        if registration_key.bean_name is not None:
            return False
        return can_substitute(registration_key.bean_contract, Converter, assume_cant_substitute=True)

    def is_registration_compatible_with_requested_key(
            self,
            requested_key: RegistrationKey,
            registered_key: RegistrationKey
    ):
        requested_converter: Converter = requested_key.bean_contract
        registered_converter: Converter = registered_key.bean_contract
        return can_substitute(requested_converter.generic_TFrom, registered_converter.generic_TFrom) \
               and can_substitute(registered_converter.generic_TTo, requested_converter.generic_TTo)

    def choose_best_candidate(
            self,
            requested_key: RegistrationKey,
            candidates: typing.OrderedDict[RegistrationKey, typing.Tuple[ContainerRegistration, IContainer]]
    ) -> typing.Optional[typing.Tuple[ContainerRegistration, IContainer]]:
        # Eliminate candidates which have more specific overrides.
        # For example, if the candidate list consists of Converter[Any, str] and Converter[int, str], then
        # Converter[Any, str] will be considered to be dominated by Converter[int, str], because it is less specific.
        # However, if we request a Converter[int, BaseClass] and the candidate list consists of
        # Converter[int, BaseClass] and Converter[int, DerivedClass], Converter[int, BaseClass] will be returned
        # because BaseClass is "closer" to the requested return type.
        is_dominated = [False for _ in candidates]
        for i, registration_key in enumerate(candidates):
            if is_dominated[i]:
                continue
            for j, other_registration_key in enumerate(candidates):
                if i == j or is_dominated[j]:
                    continue
                arg1 = registration_key.bean_contract.generic_TFrom
                arg2 = other_registration_key.bean_contract.generic_TFrom
                ret1 = registration_key.bean_contract.generic_TTo
                ret2 = other_registration_key.bean_contract.generic_TTo
                if can_substitute(arg1, arg2) \
                        and can_substitute(ret2, ret1):
                    is_dominated[j] = True

        result = [
            resolved
            for resolved, is_dominated
            in zip(candidates, is_dominated)
            if not is_dominated
        ]
        if len(result) < 1:
            return None
        elif len(result) > 1:
            raise Exception("Ambiguous resolution!")
        else:
            return candidates[result[0]]


__all__ = ["ContainerConverterResolutionPlugin"]
