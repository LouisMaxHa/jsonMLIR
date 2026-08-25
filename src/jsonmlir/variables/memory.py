from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from mlir.ir import Type

from jsonmlir.variables.struct_field import StructField

if TYPE_CHECKING:
    from jsonmlir.variables.ty.ty import TyNode
    from jsonmlir.variables.val.val import ValNode


class STRUCTS_TYPE(NamedTuple):
    NAME: str
    LLVM_TYPE: Type
    SIZE: int
    FIELDS: dict[str, StructField]


class FunctionSignature(NamedTuple):
    args: list[tuple[str, TyNode]]
    return_types: list[TyNode]


structs_type: dict[str, STRUCTS_TYPE] = {}
variables_heap: dict[str, ValNode] = {}
functions_registry: dict[str, FunctionSignature] = {}

# LMX Toujours nécéssaire ?
# Rétrocompatibilité
FIELD_TYPE = StructField

# LMX fin