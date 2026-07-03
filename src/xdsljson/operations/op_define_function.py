from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from xdsl.builder import Builder

from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.variables.memory import FunctionSignature, functions_registry
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode


class DefineFunctionOp(OpNode):
    """Déclare la signature d'une fonction (nom, types d'entrée, types de sortie).

    Ne génère aucun IR — alimente uniquement le registre global utilisé par
    CallOp pour résoudre les types de retour et vérifier les types des arguments.
    """

    op: Literal["define_function"] = "define_function"
    name: str
    args: Sequence[tuple[str, TyNode]] = ()
    return_types: Sequence[TyNode] = ()

    @trace_step("DefineFunctionOp: {self.name}")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        functions_registry[self.name] = FunctionSignature(
            args=list(self.args),
            return_types=list(self.return_types),
        )
        return []
