from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import Field

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_define_function import DefineFunctionOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_function import FunctionOp
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import functions_registry, structs_type
from jsonmlir.variables.val.val import ValNode

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
    def codegen(self) -> Sequence[ValNode]:
        structs_type.clear()
        functions_registry.clear()

        # Pré-pass : enregistrer toutes les déclarations de fonction
        # avant de générer les corps (permet les appels dans n'importe quel ordre)
        for item in self.body:
            if isinstance(item, DefineFunctionOp):
                item.codegen()

        # Passe principale : générer le reste (structs, corps de fonctions)
        for item in self.body:
            if not isinstance(item, DefineFunctionOp):
                item.codegen()

        return []
