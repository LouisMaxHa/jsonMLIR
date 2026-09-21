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

# Ptr (8 bytes) + size (8 bytes), matches std::span's {T*, size_t} layout
MDSPAN_SIZE = 8 + 8


class TyMdspan(TyNodeBase):
    """Represent a one-dimensional span descriptor containing pointer and size.

    Example:

    .. code-block:: python

       span = TyMdspan(None, TyScalar(Scalar.f64))
    """
    type: Literal["mdspan"] = "mdspan"
    dimension: int | None = Field(alias="dims")
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return [self.dimension]

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
                    type=TyPtr(TyMemref((self.dimension,), self.base)),
                    offset=0,
                    size=8,
                ),
                "size": StructAttribut(
                    name="size",
                    type=TyScalar(Scalar.i64),
                    offset=8,
                    size=8,
                ),
            },
        ))

    def __repr__(self) -> str:
        return f"Mdspanw(dims={self.dimension!r}, base={self.base!r})"
