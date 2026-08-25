from __future__ import annotations

from collections.abc import Sequence

from mlir.ir import Type, Value

from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.val.val import ValNode, ValNodeAny


class ValSSA(ValNode[TySSA]):
    # ──────────── Init ────────────
    def __init__(self, addr: Value):
        self.ty = TySSA()
        self.addr = addr

    @staticmethod
    @trace_step("ValSSA.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNodeAny
    ) -> ValSSA:
        raise ValueError("ValSSA should not be used for operations")

    # ──────────── Getter ────────────
    def get_type(self) -> Type:
        return self.addr.type

    def get_dim(self) -> Sequence[Value]:
        raise NotImplementedError("Not implemented")

    def _get_SSA(
        self,
    ) -> Value:
        return self.addr


    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNodeAny:
        raise ValueError("ValSSA should not be used for operations")


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNodeAny,
    ):
        raise ValueError("ValSSA should not be used for operations")
