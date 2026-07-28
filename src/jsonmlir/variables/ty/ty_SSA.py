from __future__ import annotations

from dataclasses import dataclass

from mlir.ir import MemRefType, Type

from jsonmlir.variables.ty.ty import TyNode


@dataclass(frozen=True)
class TySSA(TyNode):
    def get_type(self) -> Type:
        raise ValueError("SSAValue can be any type")

    def get_memref_type(self) -> MemRefType:
        raise NotImplementedError("Not implemented")

    def __repr__(self) -> str:
        return "SSA()"
