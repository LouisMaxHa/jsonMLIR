from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from xdsl.builder import Builder
from xdsl.dialects import scf
from xdsl.ir import Block, Region
from xdsl.rewriter import InsertPoint

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
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        # Condition block
        before_block = Block()
        before_builder = Builder(InsertPoint.at_end(before_block))
        conds_ssa = self.cond.codegen(before_builder)

        # Gen condition
        assert len(conds_ssa) == 1
        before_builder.insert(
            scf.ConditionOp(conds_ssa[0].get_SSA([], builder))
        )

        # After region: body + scf.yield to loop back to the before region.
        after_block, _ = codegenBlock(self.thenBlock, Block())
        after_builder = Builder(InsertPoint.at_end(after_block))
        after_builder.insert(scf.YieldOp())

        while_op = scf.WhileOp(
            [],
            [],
            Region(before_block),
            Region(after_block),
        )
        builder.insert(while_op)
        return []
