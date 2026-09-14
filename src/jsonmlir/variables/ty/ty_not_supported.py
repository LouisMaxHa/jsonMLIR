from __future__ import annotations

from typing import Any, Literal

from mlir.ir import IntegerType, MemRefType

from jsonmlir.variables.ty.ty import TyNodeBase


class TyNotSupported(TyNodeBase):
    type: Literal["notSupported"] = "notSupported"
    msg: str

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> IntegerType:
        raise TypeError(f"getType(TyNotSupported({self.msg}))")

    def get_memref_type(self) -> MemRefType:
        raise TypeError(f"get_memref_type(TyNotSupported({self.msg}))")

    def __repr__(self) -> str:
        return f"TyNotSupported({self.msg!r})"
