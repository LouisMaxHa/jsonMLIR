from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from xdsl.builder import Builder
from xdsl.dialects.builtin import ArrayAttr, StringAttr
from xdsl.dialects.llvm import LLVMStructType

from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.variables.memory import FIELD_TYPE, STRUCTS_TYPE, structs_type
from xdsljson.variables.val.val import ValNode


class DefineStructOp(OpNode):
    op: Literal["define struct"] = "define struct"
    name: str
    size: int
    fields: Sequence[FIELD_TYPE] # name, type, offset, Size

    # TODO: Need to insert it with builder ?
    @trace_step("DefineStructOp")
    def codegen(self, builder: Builder) -> Sequence[ValNode]:

        # Not already defined
        assert self.name not in structs_type.keys()

        # OpNode attribute of ValNodes
        types = [
            field.TYPE.get_type()
            for field in self.fields
        ]

        # Structure
        LLVM_TYPE = LLVMStructType(
            StringAttr(self.name),
            ArrayAttr(types),
        )
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
