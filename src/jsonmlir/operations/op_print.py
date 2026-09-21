from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mlir.dialects.func import CallOp

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


# Nom de la fonction externe (fournie par le code d'appel C++) qui imprime un entier.
PRINT_INT_SYMBOL = "print_int"


class PrintOp(OpNode):
    """Print one expression through the external ``print_int`` function.

    The generated module expects the symbol to be provided by the associated
    C++ call wrapper with ``extern "C"`` linkage.
    """

    op: Literal["print"] = "print"
    value: BaseValue

    @trace_step("PrintOp")
    def codegen(self) -> Sequence[ValNode[Any]]:
        value_ssa = self.value.codegen()
        if len(value_ssa) != 1:
            raise ValueError(
                f"print attend une seule SSAValue, en a reçu {len(value_ssa)}"
            )

        CallOp(
            [],
            PRINT_INT_SYMBOL,
            [value_ssa[0].get_SSA()],
        )
        return []
