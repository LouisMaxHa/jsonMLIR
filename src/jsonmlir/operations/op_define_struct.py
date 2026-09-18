from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import StructDescriptor, structs_registry
from jsonmlir.variables.val.struct_attribut import StructAttribut
from jsonmlir.variables.val.val import ValNode


class DefineStructOp(OpNode):
    op: Literal["define struct"] = "define struct"
    name: str
    size: int
    fields: Sequence[StructAttribut]  # name, type, offset, size

    @trace_step("DefineStructOp")
    def codegen(self) -> Sequence[ValNode[Any]]:

        # Not already defined
        assert self.name not in structs_registry.keys()


        structs_registry[self.name] = StructDescriptor(
            self.name,
            self.size,
            {
                field.name: field
                for field in self.fields
            }
        )

        # No code generated
        return []
