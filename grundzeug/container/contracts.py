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
from typing import Optional, Union, _GenericAlias

from grundzeug.container.interface import ContractT

_contract_to_type_converters = []


def register_contract_to_type_converter(converter: typing.Callable[[ContractT], Optional[type]]) -> None:
    """
    Registers a function that determines the types of non-type contracts.

    :param converter: A function that takes a contract as an argument, and returns the type of the bean that may be \
                      returned for that contract. If this converter does not support this contract, it should return \
                      ``None``.
    """
    _contract_to_type_converters.append(converter)


def convert_contract_to_type(contract: ContractT) -> Union[type, _GenericAlias, typing.Any]:
    """
    Determines the bean types from contracts using the registered contract-to-type converters.

    Please see :py:meth:`~grundzeug.container.common.register_contract_to_type_converter` for more information.

    :param contract: The contract to analyse.
    :return: The type of the bean that will be resolved for the specified contract.
    """
    if isinstance(contract, type) or isinstance(contract, _GenericAlias):
        return contract
    for converter in _contract_to_type_converters:
        res = converter(contract)
        if res is not None:
            return res
    return typing.Any


__all__ = ["register_contract_to_type_converter", "convert_contract_to_type"]
