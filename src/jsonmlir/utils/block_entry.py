from __future__ import annotations

from mlir.ir import Block, Operation


def function_entry_block(block: Block | None) -> Block:
    """Entry block of the enclosing function, not a nested scf/while/if block.
    Used to add constant values at the top of the function block so they are
    all in one place and available throughout the function.
    """
    if block is None:
        raise ValueError("function_entry_block requires a non-null block")

    owner = block.owner
    op: Operation | None = (
        owner if isinstance(owner, Operation) else owner.operation
    )
    while op is not None:
        if op.name == "func.func":
            return op.regions[0].blocks[0]
        op = op.parent

    return block
