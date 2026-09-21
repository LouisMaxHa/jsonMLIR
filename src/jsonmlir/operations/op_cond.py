from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mlir.dialects import scf
from mlir.ir import InsertionPoint

from jsonmlir.operations.block import codegenBlock
from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class IfOp(OpNode):
    """Generate a conditional block with optional then and else regions."""
    op: Literal["if"] = "if"
    cond: BaseValue
    thenBlock: Sequence[BaseValue]
    elseBlock: Sequence[BaseValue] | None = None

    @trace_step("IfOp")
    def codegen(self) -> Sequence[ValNode[Any]]:
        # Check condition
        conds_ssa = self.cond.codegen()
        assert len(conds_ssa) == 1
        cond_ssa = conds_ssa[0].get_SSA()

        # Create IfOp (les blocs then/else appartiennent à ses régions)
        has_else = self.elseBlock is not None
        if_op = scf.IfOp(cond_ssa, has_else=has_else)

        # Région then
        codegenBlock(self.thenBlock, if_op.then_block)
        scf.YieldOp([], ip=InsertionPoint(if_op.then_block))

        # Région else
        if if_op.else_block:
            codegenBlock(self.elseBlock, if_op.else_block)
            scf.YieldOp([], ip=InsertionPoint(if_op.else_block))

        return []
