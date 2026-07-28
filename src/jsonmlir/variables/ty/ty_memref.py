from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from mlir.ir import MemRefType, ShapedType

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_struct import TyStruct


@dataclass(frozen=True)
class TyMemref(TyNode):
    dimensions: Sequence[int | None]
    base: TyNode

    def get_n_elements(self) -> Sequence[int | None]:
        return self.dimensions

    def get_type(self) -> MemRefType:
        dynamic = ShapedType.get_dynamic_size()
        dimension = [d if d is not None else dynamic for d in self.dimensions]

        if isinstance(self.base, TyStruct):
            struct_size = self.base.struct.SIZE
            if dimension[-1] != dynamic:
                dimension[-1] *= struct_size
            return MemRefType.get(dimension, Scalar.i8.get_type())

        return MemRefType.get(dimension, self.base.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Memref(dims={list(self.dimensions)!r}, base={self.base!r})"
