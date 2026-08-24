from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from jsonmlir.utils.discriminants import json_op_discriminator
from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.utils import ssa_val
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA


class ConstOp(OpNode):
    """Constant value operand."""

    op: Literal["const"] = json_op_discriminator("const")
    val: float | int
    type: Scalar = Scalar.i64

    @trace_step("ConstOp: {self.val}, {self.type}")
    def codegen(self) -> Sequence[ValNode]:
        return [ValSSA(
            ssa_val.val_to_SSAValue(self.val, self.type)
        )]
