from __future__ import annotations

from typing import Any, Literal

from mlir.ir import MemRefType, Type

from jsonmlir.variables.ty.ty import TyNodeBase


class TySSA(TyNodeBase):
    type: Literal["ssa"] = "ssa"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> Type:
        raise ValueError("SSAValue can be any type")

    def get_memref_type(self) -> MemRefType:
        raise NotImplementedError("Not implemented")

    def __repr__(self) -> str:
        return "SSA()"
