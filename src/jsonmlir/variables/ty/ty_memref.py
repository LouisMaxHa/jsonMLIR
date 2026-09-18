from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

from mlir.ir import MemRefType, ShapedType
from pydantic import Field

from jsonmlir.variables.ty.ty import TyNested, TyNodeBase


class TyMemref(TyNodeBase):
    type: Literal["memref"] = "memref"
    dimensions: tuple[int | None, ...] = Field(alias="dims")
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_n_elements(self) -> Sequence[int | None]:
        return list(self.dimensions)

    def get_type(self) -> MemRefType:
        dynamic = ShapedType.get_dynamic_size()
        dimension = [d if d is not None else dynamic for d in self.dimensions]
        return MemRefType.get(dimension, self.base.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Memref(dims={list(self.dimensions)!r}, base={self.base!r})"
