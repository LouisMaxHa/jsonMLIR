from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import MemRefType
from pydantic import Field

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import StructDescriptor
from jsonmlir.variables.ty.ty import TyNested, TyNodeBase
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.struct_attribut import StructAttribut
from jsonmlir.variables.val.val_struct import ValStruct


class TyMdspan(TyNodeBase):
    type: Literal["mdspan"] = "mdspan"
    dimension: int | None = Field(alias="dims")
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return [self.dimension]

    def get_type(self) -> MemRefType:
        # Ptr (8 bytes) + padding (4 bytes) + size (4 bytes)
        return MemRefType.get([8 + 4 + 4], Scalar.i8.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def get_struct(self) -> TyStruct:
        return TyStruct(StructDescriptor(
            "None", 8 + 4 + 4, {
                "data": StructAttribut(
                    name = "data", type=TyPtr(), offset=0, size=8
                ),
                "size": StructAttribut(
                    name = "size", type=TyScalar(Scalar.i32), offset=12, size=16
                ),
            }
        ))

    def __repr__(self) -> str:
        return f"Mdspanw(dims={self.dimension!r}, base={self.base!r})"
