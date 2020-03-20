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
from typing import TYPE_CHECKING, Union, Tuple

from typing_extensions import Annotated

from grundzeug.container import ContractT
from grundzeug.container.contracts import convert_contract_to_type
from grundzeug.container.di import InjectAnnotation


class Inject():
    def __class_getitem__(self, contract: ContractT) -> Annotated:
        return Annotated[convert_contract_to_type(contract), InjectAnnotation[contract]]


class InjectNamed():
    def __class_getitem__(self, contract_and_name: Tuple[ContractT, str]) -> Annotated:
        contract, name = contract_and_name
        return Annotated[convert_contract_to_type(contract), InjectAnnotation(contract, name)]


__all__ = ["Inject", "InjectNamed"]
