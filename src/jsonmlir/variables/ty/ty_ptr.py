from __future__ import annotations

from typing import Any, Literal

from mlir.ir import IntegerType, MemRefType

from jsonmlir.variables.ty.ty import TyNested, TyNodeBase


class TyPtr(TyNodeBase):
    """Represent an address-valued pointer with a described pointee.

    You may want to use a ptr to reference a buffer of elements.
    Checks example below to choose the right one.

    Example:

    .. code-block:: python
        tyI64 = TyScalar(Scalar.i64)

        # Ptr to int: &int
        TyPtr(tyI64)

        # Ptr to array of structs : &MyStruct[]
        TyPtr(TyBuffer([none], "MyStruct"))

        # Ptr to array of int : &int[3]
        # A memref descriptor will be created for int[3] from his addr
        TyPtr(TyMemref([3], tyI64))

        # If you have a ptr to a memref descriptor, you may use
        p = Ptr(TyBuffer([1], "MemrefDescriptor"))

        # And access it with
        valSSA = p.load("*").get_SSA()
        memrefDescriptor = Factory.from_val(
            TyMemref([3], tyI64),
            valSSA
        )
        memrefDescriptor.load([2])

        # It is unlikely to be used, unless you use memref descriptors in your code.
        # You may also look at TyMdspan to have a sort-of ptr to list of element.
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
