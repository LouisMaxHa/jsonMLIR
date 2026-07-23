from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from mlir.dialects.arith import (
    AddFOp,
    AddIOp,
    AndIOp,
    CmpIOp,
    CmpIPredicate,
    DivFOp,
    DivSIOp,
    MulFOp,
    MulIOp,
    OrIOp,
    SubFOp,
    SubIOp,
    XOrIOp,
)
from mlir.ir import InsertionPoint, Value

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_operator import OperatorOp
from xdsljson.trace import trace_step
from xdsljson.utils.same_types import assert_same_types
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_SSA import ValSSA

if TYPE_CHECKING:
    from xdsljson.operations.base import BaseValue


class BinaryOp(OpNode):
    """Opération binaire composée de deux opérandes."""

    op: Literal["binary"] = "binary"
    lhs: BaseValue
    rhs: BaseValue
    ope: OperatorOp

    @trace_step("BinaryOp: {self.ope.value}")
    def codegen(self, ip: InsertionPoint) -> Sequence[ValNode]:
        lhs = self.lhs.codegen(ip)
        rhs = self.rhs.codegen(ip)

        # Check same format
        assert_same_types(lhs, rhs)

        # On applique terme à terme
        results: list[Value] = []
        for l_elem, r_elem in zip(lhs, rhs):
            l_ssa = l_elem.get_SSA([], ip)
            r_ssa = r_elem.get_SSA([], ip)

            match self.ope.value:
                case "+":
                    op = AddIOp(l_ssa, r_ssa, ip=ip)
                case "+f":
                    op = AddFOp(l_ssa, r_ssa, ip=ip)
                case "-f":
                    op = SubFOp(l_ssa, r_ssa, ip=ip)
                case "-":
                    op = SubIOp(l_ssa, r_ssa, ip=ip)
                case "*":
                    op = MulIOp(l_ssa, r_ssa, ip=ip)
                case "*f":
                    op = MulFOp(l_ssa, r_ssa, ip=ip)
                case "/":
                    op = DivSIOp(l_ssa, r_ssa, ip=ip)
                case "/f":
                    op = DivFOp(l_ssa, r_ssa, ip=ip)
                case "<" | ">" | "==" | "<=" | ">=":
                    equivalent = {
                        "<": CmpIPredicate.slt,
                        "<=": CmpIPredicate.sle,
                        ">": CmpIPredicate.sgt,
                        ">=": CmpIPredicate.sge,
                        "==": CmpIPredicate.eq,
                        "!=": CmpIPredicate.ne,
                    }
                    op = CmpIOp(equivalent[self.ope.value], l_ssa, r_ssa, ip=ip)
                case "or":
                    op = OrIOp(l_ssa, r_ssa, ip=ip)
                case "and":
                    op = AndIOp(l_ssa, r_ssa, ip=ip)
                case "xor":
                    op = XOrIOp(l_ssa, r_ssa, ip=ip)
                case _:
                    raise TypeError(f"Operator {self} not supported")

            results.append(op.result)


        return [
            ValSSA(ssa)
            for ssa in results
        ]
