from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_unary import UnaryOp
from jsonmlir.operations.op_var import VarOp
from jsonmlir.utils.trace import trace_note, trace_step
from jsonmlir.variables.factory import Factory
from jsonmlir.variables.memory import variables_heap
from jsonmlir.variables.val.val import ValNode


class SetOp(OpNode):
    """Affecte une expression à une variable."""

    op: Literal["set"] = "set"
    var: VarOp
    val: BinaryOp | ConstOp | VarOp | CallOp | UnaryOp

    @trace_step("SetOp: {self.var.name}")
    def codegen(self) -> Sequence[ValNode]:
        var = self.var.as_var()
        trace_note(f"Var: {var.get_ty()}")

        # Instantiate
        if var.get_name() not in variables_heap.keys():
            assert len(self.var.indices) == 0

            vals = self.val.codegen()
            assert len(vals) == 1
            val = vals[0]

            type = var.get_ty()
            variables_heap[var.get_name()] = Factory.from_val(type, val)
            return []

        # Store
        var.store(self.val.codegen()[0])
        return []
