from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, cast

from mlir.dialects import llvm

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import StructDescriptor, structs_type
from jsonmlir.variables.struct_field import StructField
from jsonmlir.variables.val.val import ValNodeAny


class DefineStructOp(OpNode):
    op: Literal["define struct"] = "define struct"
    name: str
    size: int
    fields: Sequence[StructField]  # name, type, offset, size

    # TODO: Need to insert it with builder ?
    @trace_step("DefineStructOp")
    def codegen(self) -> Sequence[ValNodeAny]:

        # Not already defined
        assert self.name not in structs_type.keys()

        # OpNode attribute of ValNodes
        types = [
            field.type.get_type()
            for field in self.fields
        ]

        llvmType = cast(Any, llvm.StructType).get_identified(self.name)  # type: ignore[reportAttributeAccessIssue]
        llvmType.set_body(types, packed=False)
        structs_type[self.name] = StructDescriptor(
            self.name,
            llvmType,
            self.size,
            {
                field.name: field
                for field in self.fields
            }
        )

        # No code generated
        return []
