from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode


class CommentOp(OpNode):
    """Store a message for operation-tree tracing without generating IR."""
    op: Literal["comment"] = "comment"
    msg: str

    @trace_step("Comment: {self.msg}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        return []
