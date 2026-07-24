from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from mlir.dialects import scf
from mlir.ir import InsertionPoint

from xdsljson.operations.block import codegenBlock
from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.variables.val.val import ValNode

if TYPE_CHECKING:
    from xdsljson.operations.base import BaseValue


class WhileOp(OpNode):
    op: Literal["while"] = "while"
    cond: BaseValue
    thenBlock: Sequence[BaseValue] = ()

    @trace_step("WhileOp")
    def codegen(self) -> Sequence[ValNode]:
        while_op = scf.WhileOp([], [])

        # Condition block (before region)
        before_block = while_op.before.blocks.append()
        with InsertionPoint(before_block):
            conds_ssa = self.cond.codegen()
            assert len(conds_ssa) == 1
            scf.ConditionOp(conds_ssa[0].get_SSA([]), [])

        # After region: body + scf.yield to loop back to the before region.
        after_block = while_op.after.blocks.append()
        codegenBlock(self.thenBlock, after_block)
        scf.YieldOp([], ip=InsertionPoint(after_block))

        return []
