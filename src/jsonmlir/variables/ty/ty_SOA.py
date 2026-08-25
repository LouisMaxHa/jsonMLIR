from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.ir import MemRefType, Type
from pydantic import Field

from jsonmlir.variables.ty.ty import TyNodeBase
from jsonmlir.variables.ty.ty_struct import StructRef


class TySOA(TyNodeBase):
    type: Literal["soa"] = "soa"

    # Number of struct contained
    n_elements: tuple[int | None, ...] = Field(alias="dims")
    base: StructRef

    def get_count(self) -> Sequence[int | None]:
        return list(self.n_elements)

    def get_sizes(self) -> Sequence[int | None]:
        return [
            n * self.base.struct.SIZE
            if isinstance(n, int) else None
            for n in self.n_elements
        ]

    def get_type(self) -> Type:
        raise ValueError("SOA don't have MLIR equivalent")

    def get_memref_type(self) -> MemRefType:
        raise ValueError("SOA don't have equivalent in MLIR")

    def __repr__(self) -> str:
        return f"SOA(base={self.base!r}, n_elements={list(self.n_elements)!r})"
