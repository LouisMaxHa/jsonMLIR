from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import Field
from xdsl.builder import Builder
from xdsl.dialects import memref
from xdsl.ir import SSAValue

from xdsljson.operations.codegen import OpNode
from xdsljson.operations.op_var import VarOp
from xdsljson.trace import trace_step
from xdsljson.utils.ssa_val import idx_to_ssavalues
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode


class AllocaOp(OpNode):

    op: Literal["alloca"] = "alloca"
    name: str
    type: TyNode
    size: Sequence[int | VarOp] = Field(default_factory=list[int | VarOp])

    @trace_step("AllocaOp: {self.name}")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:

        assert self.name not in variables_heap.keys()

        # Convert size to ssa
        dyn_size: list[SSAValue] = [
            idx_to_ssavalues(s, builder)
            if isinstance(s, int)
            else s.codegen()
            for s in self.size
        ]

        # Alloca
        op = memref.AllocaOp.get(
            self.type.get_memref_type().element_type,
            dynamic_sizes=dyn_size,
            shape=self.type.get_memref_type().shape
        )
        builder.insert(op)

        # Save result
        ssa = op.results[0]
        variables_heap[self.name] = Factory.from_SSA(self.type, ssa, builder)

        return [variables_heap[self.name]]
