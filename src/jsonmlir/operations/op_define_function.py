from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import FunctionSignature, functions_registry
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNode


class DefineFunctionOp(OpNode):
    """Declare a function signature for calls from generated functions.

    This operation emits no IR. It populates the registry used by ``CallOp``
    to resolve return types and validate arguments.
    """

    op: Literal["define_function"] = "define_function"
    name: str
    args: Sequence[tuple[str, TyNode]] = ()
    return_types: Sequence[TyNode] = ()

    @trace_step("DefineFunctionOp: {self.name}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        functions_registry[self.name] = FunctionSignature(
            args=list(self.args),
            return_types=list(self.return_types),
        )
        return []
