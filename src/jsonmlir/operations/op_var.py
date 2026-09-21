from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from pydantic import Field

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.var import Var


class VarOp(OpNode):
    """Load a named variable, optionally applying indices."""

    op: Literal["var"] = "var"
    name: str
    indices: Sequence[int | str | VarOp] = Field(default_factory=list)
    type: TyNode | None = None

    def as_var(self) -> Var:
        return Var(self.name, self.indices, self.type)

    # TODO: rename load to avoid confusion with get_SSA that dont use index
    @trace_step("VarOp: {self.name}, {self.indices}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        return [self.as_var().load()]
