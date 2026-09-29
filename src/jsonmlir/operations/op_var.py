from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mlir.ir import Value
from pydantic import Field

from jsonmlir.operations.codegen import Codegen
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNodeUnion
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.var import Var

if TYPE_CHECKING:
    from jsonmlir.operations.json_op import JsonOp


class VarOp(Codegen):
    """Load a named variable, optionally applying indices.
    You can set type to force type checking or let it to none and jsonMlir will try to
    deduce it from the register or other operands.

    Example:

    .. code-block:: python

        # arg is a pointeur to a array of Real3
        # Set the .x value of the 3th element to 5.0
        Set(Var("i"), ConstOp(3, "i64"))
        Set(Var("arg", ["*", Var("i"), "x"]), ConstOp(5.0, "f64"))
    """

    op: Literal["var"] = "var"
    name: str
    indices: Sequence[int | str | JsonOp] = Field(default_factory=list)
    type: TyNodeUnion | None = None

    def as_var(self) -> Var:
        # Convert indices to values
        indices: Sequence[int | str | Value] = []
        for i in self.indices:

            # op -> op.codegen[0].get_ssa()
            if isinstance(i, Codegen):
                values = i.codegen()
                assert(len(values) == 1)
                indices.append(values[0].get_SSA())

            # str -> str
            # int -> int
            else:
                indices.append(i)

        # Return var
        return Var(self.name, indices, self.type)

    # TODO: rename load to avoid confusion with get_SSA that dont use index
    @trace_step("VarOp: {self.name}, {self.indices}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        return [self.as_var().load()]
