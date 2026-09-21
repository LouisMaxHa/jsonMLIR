from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode


class NotSupportedOp(OpNode):
    """Represent an operation that has not been implemented yet."""

    op: Literal["notSupported"] = "notSupported"
    msg: str

    @trace_step("NotSupported: {self.msg}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        raise ValueError(f"NotSupported({self.msg}).codegen()")
