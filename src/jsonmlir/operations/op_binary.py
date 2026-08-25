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
from mlir.ir import Value

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.utils.trace import trace_step
from jsonmlir.utils.same_types import assert_same_types
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


def binary_codegen(
    ope: OperatorOp,
    lhs: Sequence[ValNode],
    rhs: Sequence[ValNode],
) -> Sequence[ValNode]:
    """Applique un opérateur binaire sur des opérandes déjà générés."""
    # Check same format
    assert_same_types(lhs, rhs)

    # On applique terme à terme
    results: list[Value] = []
    for l_elem, r_elem in zip(lhs, rhs):
        l_ssa = l_elem.get_SSA([])
        r_ssa = r_elem.get_SSA([])

        match ope.value:
            case "+":
                op = AddIOp(l_ssa, r_ssa)
            case "+f":
                op = AddFOp(l_ssa, r_ssa)
            case "-f":
                op = SubFOp(l_ssa, r_ssa)
            case "-":
                op = SubIOp(l_ssa, r_ssa)
            case "*":
                op = MulIOp(l_ssa, r_ssa)
            case "*f":
                op = MulFOp(l_ssa, r_ssa)
            case "/":
                op = DivSIOp(l_ssa, r_ssa)
            case "/f":
                op = DivFOp(l_ssa, r_ssa)
            case "<" | ">" | "==" | "<=" | ">=":
                equivalent = {
                    "<": CmpIPredicate.slt,
                    "<=": CmpIPredicate.sle,
                    ">": CmpIPredicate.sgt,
                    ">=": CmpIPredicate.sge,
                    "==": CmpIPredicate.eq,
                    "!=": CmpIPredicate.ne,
                }
                op = CmpIOp(equivalent[ope.value], l_ssa, r_ssa)
            case "or":
                op = OrIOp(l_ssa, r_ssa)
            case "and":
                op = AndIOp(l_ssa, r_ssa)
            case "xor":
                op = XOrIOp(l_ssa, r_ssa)
            case _:
                raise TypeError(f"Operator {ope} not supported")

        results.append(op.result)


    return [
        ValSSA(ssa)
        for ssa in results
    ]


class BinaryOp(OpNode):
    """Opération binaire composée de deux opérandes."""

    op: Literal["binary"] = "binary"
    lhs: BaseValue
    rhs: BaseValue
    ope: OperatorOp

    @trace_step("BinaryOp: {self.ope.value}")
    def codegen(self) -> Sequence[ValNode]:
        return binary_codegen(
            self.ope,
            self.lhs.codegen(),
            self.rhs.codegen(),
        )
