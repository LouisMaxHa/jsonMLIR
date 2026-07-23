from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.dialects import memref
from mlir.ir import InsertionPoint, Value
from pydantic import Field

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_var import VarOp
from xdsljson.trace import trace_step
from xdsljson.utils.ssa_val import idx_to_ssavalues
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode


class AllocOp(OpNode):

    op: Literal["alloc"] = "alloc"
    name: str
    type: TyNode
    size: Sequence[int | VarOp] = Field(default_factory=list[int | VarOp])

    @trace_step("AllocOp: {self.name}")
    def codegen(self, ip: InsertionPoint) -> Sequence[ValNode]:

        assert self.name not in variables_heap.keys()

        # Convert size to ssa
        dyn_size: list[Value] = [
            idx_to_ssavalues(s, ip)
            if isinstance(s, int)
            else s.codegen(ip)[0].get_SSA([], ip)
            for s in self.size
        ]

        # Alloc
        op = memref.AllocOp(self.type.get_memref_type(), dyn_size, [], ip=ip)

        # Save result
        ssa = op.results[0]
        variables_heap[self.name] = Factory.from_SSA(self.type, ssa, ip)

        return [variables_heap[self.name]]
