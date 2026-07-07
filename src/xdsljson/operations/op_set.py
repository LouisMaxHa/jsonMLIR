from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from xdsl.builder import Builder
from xdsl.ir import Sequence

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_call import CallOp
from xdsljson.operations.op_var import VarOp
from xdsljson.trace import trace_step
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.val.val import ValNode

if TYPE_CHECKING:
    from xdsljson.operations.op_binary import BinaryOp
    from xdsljson.operations.op_constant import ConstOp


class SetOp(OpNode):
    """Affecte une expression à une variable."""

    op: Literal["set"] = "set"
    var: VarOp
    val: BinaryOp | ConstOp | VarOp | CallOp

    @trace_step("SetOp: {self.var.name}")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        var = self.var.as_var()

        # Instantiate
        if var.get_name() not in variables_heap.keys():
            assert self.var.indices == []

            """
            # TODO: Check différence avec Version précédante:
            vals = self.val.codegen(builder)
            assert len(vals) == 1
            val = vals[0]
            """

            vals = self.val.codegen(builder)
            assert len(vals) == 1
            val = vals[0]

            type = var.get_ty()
            variables_heap[var.get_name()] = Factory.from_val(type, val, builder)
            return []

        # Store
        var.store(self.val.codegen(builder)[0], builder)
        return []
