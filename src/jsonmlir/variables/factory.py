"""Factory centralisée : création des valeurs"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mlir.ir import Value

from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_buffer import TyBuffer
from jsonmlir.variables.ty.ty_mdspan import TyMdspan
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_SOA import TySOA
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_buffer import ValBuffer
from jsonmlir.variables.val.val_mdspan import ValMdspan
from jsonmlir.variables.val.val_memref import ValMemref
from jsonmlir.variables.val.val_ptr import ValPtr
from jsonmlir.variables.val.val_scalar import ValScalar
from jsonmlir.variables.val.val_SOA import ValSOA
from jsonmlir.variables.val.val_SSA import ValSSA
from jsonmlir.variables.val.val_struct import ValStruct


class Factory:
    @staticmethod
    @trace_step("Factory.from_val", display_entry=True)
    def from_val(type: TyNode, value: ValNode[Any]) -> ValNode[Any]:
        match type:
            case TyPtr():
                return ValPtr.init_from(type, value)
            case TySSA():
                return ValSSA.init_from(type, value)
            case TyScalar():
                return ValScalar.init_from(type, value)
            case TySOA():
                return ValSOA.init_from(type, value)
            case TyStruct():
                return ValStruct.init_from(type, value)
            case TyMdspan():
                return ValMdspan.init_from(type, value)
            case TyMemref() | TyBuffer():
                return Factory.generic_memref(type.dimensions, type.base, value)
            case _:
                raise ValueError(f"From val: {type} not handled")

    @staticmethod
    @trace_step("Factory.from_SSA", display_entry=True)
    def from_SSA(type: TyNode, addr: Value) -> ValNode[Any]:
        return Factory.from_val(type, ValSSA(addr))

    @staticmethod
    @trace_step("Factory.generic_memref", display_entry=True)
    def generic_memref(
        dimensions: Sequence[int | None], base: TyNode, value: ValNode[Any]
    ) -> ValBuffer | ValMemref:
        assert len(dimensions) > 0, "Use scalar for no dimension memref"

        if isinstance(base, TyStruct):
            return ValBuffer.init_from(TyBuffer(dimensions, base), value)
        if isinstance(base, TyBuffer):
            return ValBuffer.init_from(TyBuffer(dimensions, base), value)
        return ValMemref.init_from(TyMemref(dimensions, base), value)
