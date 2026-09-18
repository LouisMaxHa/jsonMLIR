from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from jsonmlir.variables.val.struct_attribut import StructAttribut

if TYPE_CHECKING:
    from jsonmlir.variables.ty.ty import TyNode
    from jsonmlir.variables.val.val import ValNode

class StructDescriptor(NamedTuple):
    name: str
    size: int
    fields: dict[str, StructAttribut]


class FunctionSignature(NamedTuple):
    args: list[tuple[str, TyNode]]
    return_types: list[TyNode]


variables_heap: dict[str, ValNode[Any]] = {}
structs_registry: dict[str, StructDescriptor] = {}
functions_registry: dict[str, FunctionSignature] = {}

def get_available_varname(base: str) -> str:
    if base not in variables_heap.keys():
        return base

    i = 0
    while base + str(i) in variables_heap.keys():
        i += 1
    return base + str(i)