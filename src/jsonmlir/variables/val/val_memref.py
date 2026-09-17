from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mlir.dialects import memref
from mlir.ir import MemRefType, Value

from jsonmlir.utils.same_types import assert_same_shape
from jsonmlir.utils.ssa_check import all_ssavalues
from jsonmlir.utils.ssa_dim import dimensions_to_ssa
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA


class ValMemref(ValNode[TyMemref]):
    # ──────────── Init ────────────
    def __init__(self, ty: TyMemref, addr: Value):
        assert isinstance(addr.type, MemRefType)
        assert_same_shape(ty.get_type().shape, addr.type.shape)

        self.ty = ty
        self.addr = addr

    @staticmethod
    @trace_step("ValMemref.init_from", display_entry=True)
    def init_from(ty: TyMemref, source: ValNode[Any]) -> ValMemref:
        assert not isinstance(ty.base, TyStruct), "Memref of struct should use buffer"

        match source:
            case ValMemref():
                return ValMemref(ty, source.get_SSA([]))
            case ValSSA():
                return ValMemref(ty, source.get_SSA([]))
            case _:
                raise ValueError(f"Source {source} not supported")

    def __repr__(self) -> str:
        return f"ValMemref(addr, {self.ty!r})"


    # ──────────── Getter ────────────
    def get_base(self) -> TyNode:
        return self.ty.base

    def get_dim(self) -> Sequence[Value]:
        return dimensions_to_ssa(self.ty.dimensions, self.addr)

    def _get_SSA(self) -> Value:
        return self.addr

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode[Any]:
        from jsonmlir.variables.factory import Factory

        if index == []:
            return self

        # Split index
        consuming = index[: len(self.ty.dimensions)]
        remaining = index[len(self.ty.dimensions) :]
        assert all_ssavalues(consuming)

        # Load
        result_ssa = memref.LoadOp(self.addr, consuming).result
        valNode = Factory.from_SSA(self.ty.base, result_ssa)

        # Recurse
        if remaining:
            return valNode.load(remaining)
        return valNode

    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode[Any],
    ):

        # Split index
        assert len(index) >= len(self.ty.dimensions)
        consuming = index[: len(self.ty.dimensions)]
        remaining = index[len(self.ty.dimensions) :]
        assert all_ssavalues(consuming)

        # Recursive
        if remaining:
            return self.load(consuming).store(remaining, source)
        memref.StoreOp(source.get_SSA([]), self.addr, consuming)

