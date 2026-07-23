from mlir.ir import Block, Operation


def function_entry_block(block: Block | None) -> Block:
    """Bloc d'entrée de la fonction englobante (pas un bloc imbriqué scf/while/if)."""
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
