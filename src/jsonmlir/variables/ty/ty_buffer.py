from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import MemRefType, ShapedType
from pydantic import Field

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.ssa_check import all_int
from jsonmlir.variables.ty.ty import TyNodeBase
from jsonmlir.variables.ty.ty_struct import StructRef


class TyBuffer(TyNodeBase):
    """Represent a byte buffer containing contiguous struct instances.

    Example:

    .. code-block:: python

       points = TyBuffer((128,), TyStruct("Point"))
    """
    type: Literal["buffer"] = "buffer"
    dims: tuple[int | None, ...] = Field(alias="dims")
    base: StructRef # Pydantic equivalent for TyStruct

    # Constructors (``TyBuffer(dims, base)``) are handled by
    # ``TyNodeBase.__init__``; declare them here for pyright.
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> MemRefType:
        dynamic = ShapedType.get_dynamic_size()
        dimension = [d if d is not None else dynamic for d in self.dims]

        return MemRefType.get(dimension, Scalar.i8.get_type())


    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def get_n_elements(self) -> Sequence[int | None]:
        assert self.dims != ()
        if self.dims[-1] is None:
            return list(self.dims)

        # Verify last items is multiple of struct size
        assert self.dims[-1] % self.base.struct.size == 0
        n_element = self.dims[-1] // self.base.struct.size
        return list(self.dims[:-1:]) + [n_element]

    def get_bytes_size(self) -> None | int:
        if all_int(self.dims):
            return math.prod(self.dims)
        return None

    def __repr__(self) -> str:
        return f"Buffer(dims={list(self.dims)!r}, base={self.base!r})"
