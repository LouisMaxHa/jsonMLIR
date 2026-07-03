from __future__ import annotations

from typing import Literal

from xdsl.builder import Builder
from xdsl.dialects import memref
from xdsl.ir import Sequence

from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode


class AllocOp(OpNode):

    op: Literal["alloc"] = "alloc"
    name: str
    type: TyNode

    @trace_step("AllocOp: {self.name}")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:

        assert self.name not in variables_heap.keys()

        ssa = memref.alloc()

        variables_heap[self.name] = Factory.from_val(self.type, ssa, builder)

        return []
