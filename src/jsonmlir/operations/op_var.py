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
    """Load a named variable, optionally applying indices.
    You can set type to force type checking or let it to none and jsonMlir will try to deduce it from the register or other operands.

    Example:

    .. code-block:: python

        # arg is a pointeur to a array of Real3
        # Set the .x value of the 3th element to 5.0
        Set(Var("i"), ConstOp(3, "i64"))
        Set(Var("arg", ["*", Var("i"), "x"]), ConstOp(5.0, "f64"))
    """

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
