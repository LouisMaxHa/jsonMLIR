from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from mlir.dialects.func import CallOp

from jsonmlir.operations.codegen import OpNode
from jsonmlir.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


# Nom de la fonction externe (fournie par le code d'appel C++) qui imprime un entier.
PRINT_INT_SYMBOL = "print_int"


class PrintOp(OpNode):
    """Affiche la valeur d'une expression via la fonction externe ``print_int``.

    La déclaration ``func.func private @print_int(i64) -> ()`` est ajoutée
    automatiquement au module par ``compiler.declare_runtime``. Le symbole
    doit être défini dans le fichier d'appel C++ associé (par exemple
    ``examples/main.cpp``) avec un linkage ``extern "C"`` ; il est
    résolu une fois pour toutes au link statique entre le ``.o`` issu du
    pipeline jsonMLIR et l'objet du fichier d'appel.
    """

    op: Literal["print"] = "print"
    value: BaseValue

    @trace_step("PrintOp")
    def codegen(self) -> Sequence[ValNode]:
        value_ssa = self.value.codegen()
        if len(value_ssa) != 1:
            raise ValueError(
                f"print attend une seule SSAValue, en a reçu {len(value_ssa)}"
            )

        CallOp(
            [],
            PRINT_INT_SYMBOL,
            [value_ssa[0].get_SSA([])],
        )
        return []
