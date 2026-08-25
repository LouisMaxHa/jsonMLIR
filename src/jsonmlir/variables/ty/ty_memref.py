from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.ir import MemRefType, ShapedType
from pydantic import Field

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNodeBase
from jsonmlir.variables.ty.ty_struct import TyStruct


class TyMemref(TyNodeBase):
    type: Literal["memref"] = json_ty_discriminator("memref")
    dimensions: tuple[int | None, ...] = Field(alias="dims")
    base: TyNodeBase

    def get_n_elements(self) -> Sequence[int | None]:
        return list(self.dimensions)

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
