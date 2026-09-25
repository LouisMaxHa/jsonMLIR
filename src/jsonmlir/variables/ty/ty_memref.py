from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import MemRefType, ShapedType
from pydantic import Field

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNested, TyNodeBase
from jsonmlir.variables.ty.ty_struct import TyStruct

# Struct for memref, should match:
# {
#      T* allocated;         // start of the allocated storage
#      T* aligned;           // pointer to the first element
#      int64_t offset;       // shift of first element
#
#      // number of elements along each dimension
#      int64_t size[Rank];
#
#      // step between consecutive indices along each dimension,
#      // for example, if you want one element out of 2,
#      int64_t stride[Rank];
# }

class TyMemref(TyNodeBase):
    """Represent a shaped MLIR memref with a nested element type.

    Dimensions may be static integers or ``None`` for dynamic dimensions.

    Example:

    .. code-block:: python

       TyMemref((None, 3), TyScalar(Scalar.f32)) # Matrix[n][3]
    """
    type: Literal["memref"] = "memref"
    dims: tuple[int | None, ...] = Field(alias="dims")
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return list(self.dims)

    def get_type(self) -> MemRefType:
        dynamic = ShapedType.get_dynamic_size()
        dimension = [d if d is not None else dynamic for d in self.dims]

        if isinstance(self.base, TyStruct):
            struct_size = self.base.struct.size
            if dimension[-1] != dynamic:
                dimension[-1] *= struct_size
            return MemRefType.get(dimension, Scalar.i8.get_type())

        return MemRefType.get(dimension, self.base.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Memref(dims={list(self.dims)!r}, base={self.base!r})"
