from __future__ import annotations

from dataclasses import dataclass

from mlir.ir import MemRefType, Type

from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.ty.ty import TyNode


@dataclass(frozen=True)
class TyScalar(TyNode):
    scalar: Scalar

    def get_type(self) -> Type:
        return self.scalar.get_type()

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Scalar({self.scalar})"
