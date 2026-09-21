from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mlir.dialects.func import CallOp

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


# Name of the external function (provided by the C++ call wrapper) that prints an integer.
PRINT_INT_SYMBOL = "print_int"


class PrintOp(OpNode):
    """Print one expression through the external ``print_int`` function.

    The generated module expects the symbol to be provided by the associated
    C++ call wrapper with ``extern "C"`` linkage.
    Legacy function that can serve as example.

    Example:

    .. code-block:: python

       Print(Var("value"))
    """

    op: Literal["print"] = "print"
    value: BaseValue

    @trace_step("PrintOp")
    def codegen(self) -> Sequence[ValNode[Any]]:
        value_ssa = self.value.codegen()
        if len(value_ssa) != 1:
            raise ValueError(
                f"print expects a single SSAValue, received {len(value_ssa)}"
            )

        CallOp(
            [],
            PRINT_INT_SYMBOL,
            [value_ssa[0].get_SSA()],
        )
        return []
