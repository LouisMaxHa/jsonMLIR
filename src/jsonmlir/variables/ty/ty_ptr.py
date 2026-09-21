from __future__ import annotations

from typing import Any, Literal

from mlir.ir import IntegerType, MemRefType

from jsonmlir.variables.ty.ty import TyNested, TyNodeBase


class TyPtr(TyNodeBase):
    """Represent an address-valued pointer with a described pointee.

    Example:

    .. code-block:: python

       pointer = TyPtr(TyScalar(Scalar.i64))
    """
    type: Literal["ptr"] = "ptr"
    base: TyNested

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get_type(self) -> IntegerType:
        # Use i64 at the ABI boundary; the LLVM pointer appears only when
        # dereferencing.
        return IntegerType.get_signless(64)

    def get_memref_type(self) -> MemRefType:
        return MemRefType.get([], self.get_type())

    def __repr__(self) -> str:
        return f"Ptr({self.base!r})"
