from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

from mlir.ir import MemRefType, ShapedType
from pydantic import Field

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.ssa_check import all_int
from jsonmlir.variables.ty.ty import TyNodeBase
from jsonmlir.variables.ty.ty_struct import StructRef


class TyBuffer(TyNodeBase):
    type: Literal["buffer"] = json_ty_discriminator("buffer")
    dimensions: tuple[int | None, ...] = Field(alias="dims")
    base: StructRef

    def get_type(self) -> MemRefType:
        dynamic = ShapedType.get_dynamic_size()
        dimension = [d if d is not None else dynamic for d in self.dimensions]

        return MemRefType.get(dimension, Scalar.i8.get_type())


    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def get_n_elements(self) -> Sequence[int | None]:
        assert self.dimensions != ()
        if self.dimensions[-1] is None:
            return list(self.dimensions)

        # Verify last items is multiple of struct size
        assert self.dimensions[-1] % self.base.struct.SIZE == 0
        n_element = self.dimensions[-1] // self.base.struct.SIZE
        return list(self.dimensions[:-1:]) + [n_element]

    def get_bytes_size(self) -> None | int:
        if all_int(self.dimensions):
            return math.prod(self.dimensions)
        return None

    def __repr__(self) -> str:
        return f"Buffer(dims={list(self.dimensions)!r}, base={self.base!r})"
