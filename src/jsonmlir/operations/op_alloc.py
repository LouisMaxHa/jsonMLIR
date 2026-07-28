from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.dialects import memref
from mlir.ir import Value
from pydantic import Field

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_var import VarOp
from jsonmlir.trace import trace_step
from jsonmlir.utils.ssa_val import idx_to_ssavalues
from jsonmlir.variables.factory import Factory
from jsonmlir.variables.memory import variables_heap
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNode


class AllocOp(OpNode):

    op: Literal["alloc"] = "alloc"
    name: str
    type: TyNode
    size: Sequence[int | VarOp] = Field(default_factory=list[int | VarOp])

    @trace_step("AllocOp: {self.name}")
    def codegen(self) -> Sequence[ValNode]:

        assert self.name not in variables_heap.keys()

        # Convert size to ssa
        dyn_size: list[Value] = [
            idx_to_ssavalues(s)
            if isinstance(s, int)
            else s.codegen()[0].get_SSA([])
            for s in self.size
        ]

        # Alloc
        op = memref.AllocOp(self.type.get_memref_type(), dyn_size, [])

        # Save result
        ssa = op.results[0]
        variables_heap[self.name] = Factory.from_SSA(self.type, ssa)

        return [variables_heap[self.name]]
