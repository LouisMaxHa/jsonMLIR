from __future__ import annotations

from typing import Any, Literal

from mlir.ir import IntegerType, MemRefType

from jsonmlir.variables.ty.ty import TyNested, TyNodeBase


class TyPtr(TyNodeBase):
    type: Literal["ptr"] = "ptr"
    base: TyNested

    # Constructeurs positionnels gérés par ``TyNodeBase.__init__`` (voir ty_buffer.py).
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> IntegerType:
        # Adresse en i64 à la frontière ABI ; le pointeur LLVM n'apparaît
        # qu'au déréférencement.
        return IntegerType.get_signless(64)

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Ptr({self.base!r})"
