from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

from mlir.ir import Type

from jsonmlir.variables.struct_field import StructField
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.variables.ty.ty import TyNode



class StructDescriptor(NamedTuple):
    name: str
    llvmType: Type
    size: int
    fields: dict[str, StructField]


class FunctionSignature(NamedTuple):
    args: list[tuple[str, TyNode]]
    return_types: list[TyNode]


structs_type: dict[str, StructDescriptor] = {}
variables_heap: dict[str, ValNode[Any]] = {}
functions_registry: dict[str, FunctionSignature] = {}