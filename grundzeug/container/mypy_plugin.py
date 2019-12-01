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

from typing import Optional, Callable

from mypy.nodes import ClassDef, AssignmentStmt, NameExpr, CallExpr, TypeApplication, IndexExpr, TypeInfo, CastExpr, \
    Expression
from mypy.typeanal import TypeAnalyser, nongen_builtins, no_subscript_builtin_alias
from mypy.types import Type, AnyType, TypeOfAny, PlaceholderType, TypeType, Instance

from grundzeug.config.common import Configurable, configuration
from grundzeug.container.di.common import Inject

from mypy.plugin import Plugin, FunctionContext, AnalyzeTypeContext, AttributeContext, ClassDefContext

INJECT_NAME = Inject.__module__ + "." + Inject.__name__
GRUNDZEUG_CONFIG_CLASS_METADATA_KEY = "grundzeug-config"
CONFIGURABLE_NAME = Configurable.__module__ + "." + Configurable.__name__
CONFIGURATION_NAME = configuration.__module__ + "." + configuration.__name__


class GrundzeugContainerMypyPlugin(Plugin):

    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        def process_configuration_class(context: ClassDefContext):
            cls: ClassDef = context.cls
            cls.info.metadata[GRUNDZEUG_CONFIG_CLASS_METADATA_KEY] = {}
            for statement in cls.defs.body:
                # Ensure that the left
                if not isinstance(statement, AssignmentStmt):
                    continue

                statement: AssignmentStmt = statement

                # Ensure that the left expression is a name expression. Simultaneous assignment is not supported.
                if len(statement.lvalues) != 1:
                    continue
                if not isinstance(statement.lvalues[0], NameExpr):
                    continue
                field_name_expr: NameExpr = statement.lvalues[0]

                # We only support function calls on the right hand side.
                if not isinstance(statement.rvalue, CallExpr):
                    continue
                call_expr: CallExpr = statement.rvalue

                sym = cls.info.names.get(field_name_expr.name)
                if sym is None:
                    continue

                node = sym.node

                # We only support syntax like Configurable[ContractT](...).
                # The callee is actually an index expression: Configurable[ContractT].
                if not isinstance(call_expr.callee, IndexExpr):
                    continue
                callee: IndexExpr = call_expr.callee

                # Ensure that we are processing a Configurable element.
                if not isinstance(callee.base, NameExpr):
                    continue
                if not hasattr(callee.base, "name") or (callee.base.fullname != CONFIGURABLE_NAME):
                    continue

                # Infer the type enclosed in the square brackets
                if not isinstance(callee.index.node, TypeInfo):
                    continue

                field_type = Instance(callee.index.node, [])
                node.type = field_type
                statement.rvalue = CastExpr(statement.rvalue, field_type)

        if fullname == CONFIGURATION_NAME:
            return process_configuration_class
        return None

    def get_type_analyze_hook(self, fullname):
        def _try_find_configuration_property(api, inject_contract_type):
            if not hasattr(inject_contract_type, "name"):
                return False, None

            # Try to look up the field.
            symbol = api.lookup_qualified(inject_contract_type.name, inject_contract_type, suppress_errors=True)
            if symbol is None:
                return False, None

            # Here, symbol is supposed to be Mdef/Var referring to a field in a configuration class.

            # Find the TypeInfo for the configuration class.
            if hasattr(symbol.node, "info"):
                info_class_info = symbol.node.info
            else:
                info_class_info = symbol.node

            # Configuration classes are supposed to have a GRUNDZEUG_CONFIG_CLASS_METADATA_KEY key in the metadata.
            if not hasattr(info_class_info, "metadata"):
                return False, None

            if GRUNDZEUG_CONFIG_CLASS_METADATA_KEY in info_class_info.metadata:
                # Return the type of the configuration field.
                node = symbol.node
                return True, node.type

            return False, None

        def _analyze_injection(context):
            api: TypeAnalyser = context.api
            arg_count = len(context.type.args)
            if arg_count != 1:
                api.fail(f"Grundzeug Inject takes 1 argument, {arg_count} given.", context.type)
            requested_contract = context.type.args[0]
            success, new_requested_contract = _try_find_configuration_property(api, requested_contract)
            if success:
                return api.anal_type(new_requested_contract)
            return api.anal_type(requested_contract)

        if fullname == INJECT_NAME:
            return _analyze_injection
        return None


def plugin(version):
    return GrundzeugContainerMypyPlugin
