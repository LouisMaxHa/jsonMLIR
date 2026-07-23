from __future__ import annotations

from typing import NamedTuple

from mlir.ir import Type

from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode


class FIELD_TYPE(NamedTuple):
    NAME: str
    TYPE: TyNode
    OFFSET: int
    SIZE: int


class STRUCTS_TYPE(NamedTuple):
    NAME: str
    LLVM_TYPE: Type
    SIZE: int
    FIELDS: dict[str, FIELD_TYPE]


class FunctionSignature(NamedTuple):
    args: list[tuple[str, TyNode]]
    return_types: list[TyNode]


structs_type: dict[str, STRUCTS_TYPE] = {}
variables_heap: dict[str, ValNode] = {}
functions_registry: dict[str, FunctionSignature] = {}
