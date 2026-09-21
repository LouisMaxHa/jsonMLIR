from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils import ssa_val
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA


class ConstOp(OpNode):
    """Constant value operand.

    Constants are defined at the top of function declaration and reuse if saved value.
    If no type is precised, `i64`, `i1` or `f64` can be deduced.

    Example:

    .. code-block:: python

        # Equivalent
        Const(true)
        Const(true, Scalar.i1)

        Const(42)
        Const(42, Scalar.i64)
    """

    op: Literal["const"] = "const"
    val: float | int | bool
    type: Scalar | None = None

    @trace_step("ConstOp: {self.val}, {self.type}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        type = self.type
        val = self.val

        if type is None and isinstance(val, float):
            type = Scalar.f64
        if type is None and isinstance(val, int):
            type = Scalar.i64
        if type is None and isinstance(val, bool):
            type = Scalar.i1

        assert type is not None
        return [ValSSA(
            ssa_val.val_to_SSAValue(val, type)
        )]
