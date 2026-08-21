from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from mlir.ir import Block, InsertionPoint

from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue

# TODO: On renvoie automatiquement la dernière valeur,
# mais utiliser plutôt yield
@trace_step("CodegenBlock", display_entry=True)
def codegenBlock(
    content: Sequence[BaseValue] | None,
    block: Block,
) -> tuple[Block, Sequence[ValNode]]:

    # Gen block
    if content is None:
        return block, []

    # Populate block
    last_value: Sequence[ValNode] = []
    with InsertionPoint(block):
        for element in content:
            last_value = element.codegen()

    return block, last_value
