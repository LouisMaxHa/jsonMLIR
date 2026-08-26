from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from mlir.dialects import scf
from mlir.ir import InsertionPoint

from jsonmlir.operations.block import codegenBlock
from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNodeAny

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class WhileOp(OpNode):
    op: Literal["while"] = "while"
    cond: BaseValue
    thenBlock: Sequence[BaseValue] = ()

    @trace_step("WhileOp")
    def codegen(self) -> Sequence[ValNodeAny]:
        while_op = scf.WhileOp([], [])

        # Condition block (before region)
        before_block = while_op.before.blocks.append()  # type: ignore[reportUnknownMemberType]
        with InsertionPoint(before_block):
            conds_ssa = self.cond.codegen()
            assert len(conds_ssa) == 1
            scf.ConditionOp(conds_ssa[0].get_SSA([]), [])

        # After region: body + scf.yield to loop back to the before region.
        after_block = while_op.after.blocks.append()  # type: ignore[reportUnknownMemberType]
        codegenBlock(self.thenBlock, after_block)
        scf.YieldOp([], ip=InsertionPoint(after_block))

        return []
