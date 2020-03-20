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

from inspect import Signature
from typing import Dict, Any

from grundzeug.container.interface import IContainer
from grundzeug.container.di.common import TypeIntrospector, InjectAnnotation, register_type_introspector


class DefaultTypeIntrospector(TypeIntrospector):

    def inject_fields(self, type_, instance, container: IContainer):
        for k, v in type_.__dict__.items():
            if not isinstance(v, InjectAnnotation):
                continue
            setattr(
                instance,
                k,
                container.resolve_bean(
                    contract=v.bean_contract,
                    bean_name=v.bean_name
                )
            )

    def get_kwargs_to_inject(self, func, signature: Signature, container: IContainer) -> Dict[str, Any]:
        return {
            k: container.resolve_bean(
                contract=v.default.bean_contract,
                bean_name=v.default.bean_name
            )
            for k, v
            in signature.parameters.items()
            if isinstance(v.default, InjectAnnotation)
        }


register_type_introspector(DefaultTypeIntrospector())

__all__ = ["DefaultTypeIntrospector"]
