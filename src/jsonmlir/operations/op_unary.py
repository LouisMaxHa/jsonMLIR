from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class UnaryOperator(Enum):
    """Unary operators supported by :class:`UnaryOp`."""

    negOp = "-"
    negFOp = "-f"
    notOp = "!"


class UnaryOp(OpNode):
    """Apply a unary operator, lowered to a binary operation with a constant."""

    op: Literal["unary"] = "unary"
    ope: UnaryOperator
    value: BaseValue

    @trace_step("UnaryOp: {self.ope.value}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        match self.ope:
            # -f x  ->  x *f -1.0
            case UnaryOperator.negFOp:
                return BinaryOp(
                    lhs = self.value,
                    rhs = ConstOp(val=-1.0, type=Scalar.f64),
                    ope = OperatorOp.timesFOp
                ).codegen()
            # -  x  ->  x  * -1
            case UnaryOperator.negOp:
                return BinaryOp(
                    lhs = self.value,
                    rhs = ConstOp(val=-1, type=Scalar.i64),
                    ope = OperatorOp.timesOp
                ).codegen()
            # !x    ->  x xor true
            case UnaryOperator.notOp:
                return BinaryOp(
                    lhs = self.value,
                    rhs = ConstOp(val=1, type=Scalar.i1),
                    ope = OperatorOp.xorOp
                ).codegen()
