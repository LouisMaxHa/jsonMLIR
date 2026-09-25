from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import MemRefType
from pydantic import Field

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import StructDescriptor
from jsonmlir.variables.ty.ty import TyNested, TyNodeBase
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.struct_attribut import StructAttribut

# Pointer size in the target ABI. The dimension fields can be i32 or i64.
MDSPAN_POINTER_SIZE = 8
MDSPAN_SIZE = MDSPAN_POINTER_SIZE + 8  # Legacy 1D i64 descriptor size.
MDSPAN_SIZE_ATTR_NAME: str = "sizeFirstDimension"

class TyMdspan(TyNodeBase):
    """Represent a row-major span descriptor containing pointer and extents.

    Example:

    .. code-block:: python

       TyMdspan((None,), TyScalar(Scalar.f64))
       TyMdspan((None, None), TyScalar(Scalar.f64), index_type=Scalar.i32)
    """
    type: Literal["mdspan"] = "mdspan"
    dims: tuple[int | None, ...] = Field(alias="dims")
    base: TyNested
    index_type: Literal[Scalar.i32, Scalar.i64] = Scalar.i64

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return list(self.dims)

    def get_type(self) -> MemRefType:
        return MemRefType.get([MDSPAN_SIZE], Scalar.i8.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def get_struct(self) -> TyStruct:
        return TyStruct(StructDescriptor(
            "mdspan",
            MDSPAN_SIZE,
            {
                "data": StructAttribut(
                    name="data",
                    type=TyPtr(TyMemref((None,), self.base)),
                    offset=0,
                    size=MDSPAN_POINTER_SIZE,
                ),
                MDSPAN_SIZE_ATTR_NAME: StructAttribut(
                    name=MDSPAN_SIZE_ATTR_NAME,
                    type=TyScalar(self.index_type),
                    offset= 8 if (self.index_type == Scalar.i64) else 12,
                    size  = 8 if (self.index_type == Scalar.i64) else 4
                )
            })
        )

    def __repr__(self) -> str:
        return (
            f"Mdspan(dims={list(self.dims)!r}, base={self.base!r}, "
            f"index_type={self.index_type!r})"
        )
