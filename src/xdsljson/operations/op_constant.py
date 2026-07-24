from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.utils import ssa_val
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_SSA import ValSSA


class ConstOp(OpNode):
    """Constant value operand."""

    op: Literal["const"] = "const"
    val: float | int
    type: Scalar = Scalar.i64

    @trace_step("ConstOp: {self.val}, {self.type}")
    def codegen(self) -> Sequence[ValNode]:
        return [ValSSA(
            ssa_val.val_to_SSAValue(self.val, self.type)
        )]
