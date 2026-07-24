from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_binary import BinaryOp
from xdsljson.operations.op_call import CallOp
from xdsljson.operations.op_constant import ConstOp
from xdsljson.operations.op_var import VarOp
from xdsljson.trace import trace_step
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.val.val import ValNode


class SetOp(OpNode):
    """Affecte une expression à une variable."""

    op: Literal["set"] = "set"
    var: VarOp
    val: BinaryOp | ConstOp | VarOp | CallOp

    @trace_step("SetOp: {self.var.name}")
    def codegen(self) -> Sequence[ValNode]:
        var = self.var.as_var()

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
