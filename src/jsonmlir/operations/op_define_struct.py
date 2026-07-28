from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.dialects import llvm

from jsonmlir.operations.codegen import OpNode
from jsonmlir.trace import trace_step
from jsonmlir.variables.memory import FIELD_TYPE, STRUCTS_TYPE, structs_type
from jsonmlir.variables.val.val import ValNode


class DefineStructOp(OpNode):
    op: Literal["define struct"] = "define struct"
    name: str
    size: int
    fields: Sequence[FIELD_TYPE] # name, type, offset, Size

    # TODO: Need to insert it with builder ?
    @trace_step("DefineStructOp")
    def codegen(self) -> Sequence[ValNode]:

        # Not already defined
        assert self.name not in structs_type.keys()

        # OpNode attribute of ValNodes
        types = [
            field.TYPE.get_type()
            for field in self.fields
        ]

        # Structure
        LLVM_TYPE = llvm.StructType.get_identified(self.name)
        LLVM_TYPE.set_body(types, packed=False)
        structs_type[self.name] = STRUCTS_TYPE(
            self.name,
            LLVM_TYPE,
            self.size,
            {
                field.NAME: field
                for field in self.fields
            }
        )

        # No code generated
        return []
