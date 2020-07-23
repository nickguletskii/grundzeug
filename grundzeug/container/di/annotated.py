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
from typing import Dict, Any, Generator

from typing_extensions import Annotated

from grundzeug.container.di import Inject
from grundzeug.container.di.common import InjectAnnotation, TypeIntrospector, register_type_introspector
from grundzeug.container.interface import IContainer


class AnnotatedTypeIntrospector(TypeIntrospector):
    def _process(self, annotated_type: Annotated) -> Generator[InjectAnnotation, None, None]:
        matching_annotations = [
            item
            for item
            in annotated_type.__metadata__
            if isinstance(item, InjectAnnotation)
               or item == Inject
               or item == InjectAnnotation
        ]
        if len(matching_annotations) == 0:
            return

        if len(matching_annotations) > 1:
            raise Exception("InjectAnnotation has been specified twice.")

        if matching_annotations[0] == Inject or matching_annotations[0] == InjectAnnotation:
            yield InjectAnnotation(contract=annotated_type.__origin__)
            return

        yield matching_annotations[0]

    def inject_fields(self, type_, instance, container: IContainer):
        field_defs = type_.__dict__.get('__annotations__', {})
        for k, v in field_defs.items():
            if not hasattr(v, "__metadata__"):
                continue

            for annotation in self._process(annotated_type=v):
                setattr(
                    instance,
                    k,
                    container.resolve_bean(
                        contract=annotation.bean_contract,
                        bean_name=annotation.bean_name
                    )
                )

    def get_kwargs_to_inject(self, func, signature: Signature, container: IContainer) -> Dict[str, Any]:
        return {
            k: container.resolve_bean(
                contract=annotation.bean_contract,
                bean_name=annotation.bean_name
            )
            for k, v
            in signature.parameters.items()
            if hasattr(v.annotation, "__metadata__")
            for annotation
            in self._process(annotated_type=v.annotation)
        }


register_type_introspector(AnnotatedTypeIntrospector())

__all__ = ["AnnotatedTypeIntrospector"]
