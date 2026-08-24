from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Literal

from mlir.dialects.math import SqrtOp

from jsonmlir.utils.discriminants import json_op_discriminator
from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class MathOperator(Enum):
    sqrtOp = "sqrt"

class MathOp(OpNode):
    """Opération binaire composée de deux opérandes."""

    op: Literal["math"] = json_op_discriminator("math")
    ope: MathOperator
    value: BaseValue

    @trace_step("MathOp: {self.ope.value}")
    def codegen(self) -> Sequence[ValNode]:
        value = self.value.codegen()
        value_ssa = value[0].get_SSA([])

        match self.ope.value:
            case "sqrt":
                op = SqrtOp(value_ssa)

        return [
            ValSSA(op.result)
        ]
