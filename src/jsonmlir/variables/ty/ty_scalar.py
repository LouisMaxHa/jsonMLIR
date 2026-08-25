from __future__ import annotations

from typing import Any, Literal

from mlir.ir import MemRefType, Type
from pydantic import Field

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNodeBase


class TyScalar(TyNodeBase):
    type: Literal["scalar"] = "scalar"
    scalar: Scalar = Field(alias="name")

    # Constructeurs positionnels gérés par ``TyNodeBase.__init__`` (voir ty_buffer.py).
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> Type:
        return self.scalar.get_type()

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Scalar({self.scalar})"
