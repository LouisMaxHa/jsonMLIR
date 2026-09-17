from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import IntegerType, MemRefType
from pydantic import Field

from jsonmlir.variables.memory import StructDescriptor
from jsonmlir.variables.ty.ty import TyNested, TyNodeBase
from jsonmlir.variables.ty.ty_struct import TyStruct


class TyMdspan(TyNodeBase):
    type: Literal["mdspan"] = "mdspan"
    dimension: int | None = Field(alias="dims")
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return [self.dimension]

    def get_struct(self) -> TyStruct:
      return TyStruct(StructDescriptor(
        
      ))


    def get_type(self) -> MemRefType:
        byteSize = 8 + 4 + 4 # ptr + padding + nElems
        return MemRefType.get([byteSize], IntegerType.get_signless(8))

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Mdspan(dim={self.dimension!r}, base={self.base!r})"
