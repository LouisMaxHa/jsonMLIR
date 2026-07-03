from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import Field
from xdsl.builder import Builder

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_define_function import DefineFunctionOp
from xdsljson.operations.op_define_struct import DefineStructOp
from xdsljson.operations.op_function import FunctionOp
from xdsljson.trace import trace_step
from xdsljson.variables.memory import functions_registry, structs_type
from xdsljson.variables.val.val import ValNode

# Déclaration de struct, de signature de fonction, ou de corps de fonction
ModuleStatement = Annotated[
    DefineStructOp | DefineFunctionOp | FunctionOp,
    Field(discriminator="op"),
]


class ModuleJsonOp(OpNode):
    """Racine JSON de type module : enregistre les structs puis génère les fonctions."""

    op: Literal["module"] = "module"
    body: Sequence[ModuleStatement] = ()

    @trace_step("ModuleJsonOp")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        structs_type.clear()
        functions_registry.clear()

        # Pré-pass : enregistrer toutes les déclarations de fonction
        # avant de générer les corps (permet les appels dans n'importe quel ordre)
        for item in self.body:
            if isinstance(item, DefineFunctionOp):
                item.codegen(builder)

        # Passe principale : générer le reste (structs, corps de fonctions)
        for item in self.body:
            if not isinstance(item, DefineFunctionOp):
                item.codegen(builder)

        return []
