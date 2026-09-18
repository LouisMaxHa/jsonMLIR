from __future__ import annotations

from collections.abc import Callable
from typing import Any

from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_struct import ValStruct

# Indexing handler : (struct, index) -> ValNode
StructIndexing = Callable[[ValStruct, str | int], ValNode[Any]]

REGISTER_INDEXING: dict[str, StructIndexing] = {}

def struct_index(struct_name: str) -> Callable[[StructIndexing], StructIndexing]:
    """Custom indexing operator for structure"""

    def register(fn: StructIndexing) -> StructIndexing:
        REGISTER_INDEXING[struct_name] = fn
        return fn

    return register


def call_structure_index(
    struct: ValStruct, index: str | int
) -> ValNode[Any]:
    handler = REGISTER_INDEXING.get(struct.ty.name)
    if handler is None:
        raise NotImplementedError(
            f"Struct {struct.ty.name!r} does not implement custom index operator"
        )
    return handler(struct, index)



# ──────────── Methodes ────────────
@struct_index("mdspan")
def _real3_operator(
    struct: ValStruct, index: str | int
) -> ValNode[Any]:
  assert isinstance(index, int)
  return struct.get_field("data").load([index])
