from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from jsonmlir.utils.discriminants import json_op_discriminator
from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.var import Var


class VarOp(OpNode):
    op: Literal["var"] = json_op_discriminator("var")
    name: str
    indices: Sequence[int | str | VarOp] = Field(default_factory=list)
    type: TyNode | None = None

    def as_var(self) -> Var:
        return Var(self.name, self.indices, self.type)

    # TODO: rename load to avoid confusion with get_SSA that dont use index
    @trace_step("VarOp: {self.name}, {self.indices}")
    def codegen(self) -> Sequence[ValNode]:
        return [self.as_var().load()]
