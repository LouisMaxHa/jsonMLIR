from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

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

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.utils.same_types import assert_same_val
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.struct_method import call_structure_method
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA
from jsonmlir.variables.val.val_struct import ValStruct

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue

class BinaryOp(OpNode):
    """Apply an operator to two operands element by element.

    Scalar operations are lowered to the matching arithmetic or comparison operation.
    Struct operands are dispatched to their registered methods
    defined in variables/val/struct_method.

    Supported binary operators are listed in `OperatorOp` enum:
    `+`, `+f`, `-f`, `-`, `*`, `*f`, `/`, `/f`, `<`, `>`, `==`, `<=`, `>=`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `or`, `and`, `xor`

    Example:

    .. code-block:: python

       Binary("+", Var("lhs"), Var("rhs"))
    """

    op: Literal["binary"] = "binary"
    lhs: BaseValue
    rhs: BaseValue
    ope: OperatorOp

    @trace_step("BinaryOp: {self.ope.value}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        """Apply an operator."""
        # Recursive codegen
        l_vals = self.lhs.codegen()
        r_vals = self.rhs.codegen()

        # Apply element by element.
        results: list[ValNode[Any]] = []
        for l_val, r_val in zip(l_vals, r_vals):

            # Structs: delegate to the handler registered for the structure.
            if isinstance(l_val, ValStruct) or isinstance(r_val, ValStruct):
                struct_val = l_val if isinstance(l_val, ValStruct) else r_val
                assert isinstance(struct_val, ValStruct)
                results.append(
                    call_structure_method(struct_val.ty.name, self.ope, l_val, r_val)
                )
                continue

            # Scalars
            results.append(generate_bin_op(self.ope, l_val, r_val))
        return results


def generate_bin_op(ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]
) -> ValNode[Any]:
    assert_same_val(lhs, rhs)
    l_ssa = lhs.get_SSA()
    r_ssa = rhs.get_SSA()
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
    return ValSSA(op.result)
