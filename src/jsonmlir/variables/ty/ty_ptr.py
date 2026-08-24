from __future__ import annotations

from typing import Literal

from mlir.ir import IntegerType, MemRefType

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.variables.ty.ty import TyNode


class TyPtr(TyNode):
    type: Literal["ptr"] = json_ty_discriminator("ptr")
    base: TyNode

    def get_type(self) -> IntegerType:
        # Adresse en i64 à la frontière ABI ; le pointeur LLVM n'apparaît
        # qu'au déréférencement.
        return IntegerType.get_signless(64)

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Ptr({self.base!r})"
