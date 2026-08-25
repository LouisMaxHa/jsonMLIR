from __future__ import annotations

from typing import Literal

from mlir.ir import MemRefType, Type

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.variables.ty.ty import TyNodeBase


class TySSA(TyNodeBase):
    type: Literal["ssa"] = json_ty_discriminator("ssa")

    def get_type(self) -> Type:
        raise ValueError("SSAValue can be any type")

    def get_memref_type(self) -> MemRefType:
        raise NotImplementedError("Not implemented")

    def __repr__(self) -> str:
        return "SSA()"
