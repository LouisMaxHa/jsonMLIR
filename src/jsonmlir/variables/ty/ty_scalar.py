from __future__ import annotations

from typing import Literal

from mlir.ir import MemRefType, Type
from pydantic import Field

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNodeBase


class TyScalar(TyNodeBase):
    type: Literal["scalar"] = json_ty_discriminator("scalar")
    scalar: Scalar = Field(alias="name")

    def get_type(self) -> Type:
        return self.scalar.get_type()

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Scalar({self.scalar})"
