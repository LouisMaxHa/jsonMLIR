"""Factory centralisée : création et enregistrement des ValNodes dans le heap."""

from __future__ import annotations

from collections.abc import Sequence

from mlir.ir import InsertionPoint, Value

from xdsljson.trace import trace_step
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.ty.ty_buffer import TyBuffer
from xdsljson.variables.ty.ty_memref import TyMemref
from xdsljson.variables.ty.ty_ptr import TyPtr
from xdsljson.variables.ty.ty_scalar import TyScalar
from xdsljson.variables.ty.ty_SOA import TySOA
from xdsljson.variables.ty.ty_SSA import TySSA
from xdsljson.variables.ty.ty_struct import TyStruct
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_buffer import ValBuffer
from xdsljson.variables.val.val_memref import ValMemref
from xdsljson.variables.val.val_ptr import ValPtr
from xdsljson.variables.val.val_scalar import ValScalar
from xdsljson.variables.val.val_SOA import ValSOA
from xdsljson.variables.val.val_SSA import ValSSA
from xdsljson.variables.val.val_struct import ValStruct


class Factory:
    @staticmethod
    @trace_step("Factory.from_val", display_entry=True)
    def from_val(type: TyNode, value: ValNode, ip: InsertionPoint) -> ValNode:
        match type:
            case TyPtr():
                return ValPtr.init_from(type, value, ip)
            case TySSA():
                return ValSSA.init_from(type, value, ip)
            case TyScalar():
                return ValScalar.init_from(type, value, ip)
            case TyMemref():
                return ValMemref.init_from(type, value, ip)
            case TyBuffer():
                return ValBuffer.init_from(type, value, ip)
            case TySOA():
                return ValSOA.init_from(type, value, ip)
            case TyStruct():
                return ValStruct.init_from(type, value, ip)
            case _:
                raise ValueError("From val: Type not handled")

    @staticmethod
    @trace_step("Factory.from_SSA", display_entry=True)
    def from_SSA(type: TyNode, addr: Value, ip: InsertionPoint) -> ValNode:
        return Factory.from_val(type, ValSSA(addr), ip)

    @staticmethod
    @trace_step("Factory.generic_memref", display_entry=True)
    def generic_memref(
        dimensions: Sequence[int | None], base: TyNode, addr: Value
    ) -> ValBuffer | ValMemref:
        assert len(dimensions) > 0

        if isinstance(base, TyStruct):
            return ValBuffer(TyBuffer(dimensions, base), addr)
        if isinstance(base, TyBuffer):
            return ValBuffer(base, addr)
        return ValMemref(TyMemref(dimensions, base), addr)
