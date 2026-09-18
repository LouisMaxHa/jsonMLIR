from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mlir.ir import MemRefType, Value

from jsonmlir.utils.same_types import assert_same_shape
from jsonmlir.utils.ssa_dim import dimensions_to_ssa
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_mdspan import TyMdspan
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA
from jsonmlir.variables.val.val_struct import ValStruct


class ValMdspan(ValNode[TyMdspan]):
    # ──────────── Init ────────────
    def __init__(self, ty: TyMdspan, addr: Value):
        assert isinstance(addr.type, MemRefType)
        assert_same_shape(ty.get_type().shape, addr.type.shape)

        self.ty = ty
        self.addr = addr

    @staticmethod
    @trace_step("ValMdspan.init_from", display_entry=True)
    def init_from(ty: TyMdspan, source: ValNode[Any]) -> ValMdspan:
        assert isinstance(source, (ValSSA, ValMdspan)), f"Got {source}"
        return ValMdspan(ty, source.get_SSA([]))

    def __repr__(self) -> str:
        return f"ValMdspan(addr, {self.ty!r})"


    # ──────────── Getter ────────────
    def get_base(self) -> TyNode:
        return self.ty.base

    def get_struct(self) -> ValStruct:
        return ValStruct(self.ty.get_struct(), self.addr)

    def get_dim(self) -> Sequence[Value]:
        return dimensions_to_ssa([self.ty.dimension], self.addr)

    def _get_SSA(self) -> Value:
        return self.addr

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode[Any]:
        if index == []:
            return self

        # str   -> consider struct
        # Value -> load data and apply
        if isinstance(index[0], Value):
            return self.get_struct().load(["data", "*"] + list(index))
        return self.get_struct().load(index)



    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode[Any],
    ):
        assert(len(index) > 0)
        # int -> load data and apply
        # str -> consider struct
        match index[0]:
            case int():
                return self.get_struct().store(["data", "*"] + list(index), source)
            case str():
                return self.get_struct().store(index, source)

