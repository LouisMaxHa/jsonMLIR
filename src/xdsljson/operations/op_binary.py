from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from xdsl.builder import Builder
from xdsl.dialects.arith import (
    AddfOp,
    AddiOp,
    AndIOp,
    CmpiOp,
    DivSIOp,
    MulfOp,
    MuliOp,
    OrIOp,
    SubfOp,
    SubiOp,
    XOrIOp,
    DivfOp
)
from xdsl.ir import Attribute, OpResult

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
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        lhs = self.lhs.codegen(builder)
        rhs = self.rhs.codegen(builder)

        # Check same format
        assert_same_types(lhs, rhs)

        # On applique terme à terme
        results: Sequence[OpResult[Attribute]] = []
        for l_elem, r_elem in zip(lhs, rhs):
            l_ssa = l_elem.get_SSA([], builder)
            r_ssa = r_elem.get_SSA([], builder)

            match self.ope.value:
                case "+":
                    op = AddiOp(l_ssa, r_ssa)
                case "+f":
                    op = AddfOp(l_ssa, r_ssa)
                case "-f":
                    op = SubfOp(l_ssa, r_ssa)
                case "-":
                    op = SubiOp(l_ssa, r_ssa)
                case "*":
                    op = MuliOp(l_ssa, r_ssa)
                case "*f":
                    op = MulfOp(l_ssa, r_ssa)
                case "/":
                    op = DivSIOp(l_ssa, r_ssa)
                case "/f":
                    op = DivfOp(l_ssa, r_ssa)
                case "<" | ">" | "==" | "<=" | ">=":
                    equivalent = {
                        "<": "slt",
                        "<=": "sle",
                        ">": "sgt",
                        ">=": "sge",
                        "==": "eq",
                        "!=": "neq",
                    }
                    op = CmpiOp(l_ssa, r_ssa, equivalent[self.ope.value])
                case "or":
                    op = OrIOp(l_ssa, r_ssa)
                case "and":
                    op = AndIOp(l_ssa, r_ssa)
                case "xor":
                    op = XOrIOp(l_ssa, r_ssa)
                case _:
                    raise TypeError(f"Operator {self} not supported")

            builder.insert(op)
            results.append(op.result)


        return [
            ValSSA(ssa)
            for ssa in results
        ]
