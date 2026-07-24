from __future__ import annotations

from collections.abc import Sequence
from decimal import InvalidOperation

from mlir.ir import Type, Value

from xdsljson.trace import trace_step
from xdsljson.variables.memory import STRUCTS_TYPE
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.ty.ty_buffer import TyBuffer
from xdsljson.variables.ty.ty_SOA import TySOA
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_buffer import ValBuffer
from xdsljson.variables.val.val_memref import ValMemref


class ValSOA(ValNode):
    """Vue Structure-of-Arrays : une colonne memref strided par attribut."""

    addrs: dict[str, ValMemref | ValBuffer]
    ty: TySOA

    # ──────────── Init ────────────
    def __init__(self, ty: TySOA, addrs: dict[str, ValMemref | ValBuffer]):
        # Résolution différée : le struct doit exister à l'exécution
        # assert ty.base in structs_type.keys()

        # Each array should have correct number of elements
        for addr in addrs.values():
            assert addr.get_ty().get_n_elements() == list(ty.n_elements), f"Got {addr.get_ty().get_n_elements()}, expected {ty.n_elements}"

        self.addrs = addrs
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValSOA(addrs={list(self.addrs.keys())}, ty={self.ty!r})"

    # ──────────── Getter ────────────
    def get_ty(self) -> TySOA:
        return self.ty

    def get_type(self) -> Type:
        raise ValueError("SOA don't have equivalent in MLIR")

    # WARN: Should return number of elements ? Or can return DYNAMIC ?
    def get_dim(self) -> Sequence[Value]:
        raise NotImplementedError

    def get_SSA(
        self, index: Sequence[str | Value | int]
    ) -> Value:
        assert len(index) >= 1
        assert isinstance(index[0], str)
        assert index[0] in self.ty.base.struct.FIELDS

        consumming = index[0]
        remaining = index[1::]
        return self.load([consumming]).get_SSA(remaining)

    def _get_SSA(
        self,
    ) -> Value:
        raise InvalidOperation(
            "ValScalar don't have SSA equivalent.Use get_SSA with attribut str"
        )

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode:

        assert len(index) >= 1
        assert isinstance(index[0], str)
        assert index[0] in self.ty.base.struct.FIELDS

        # Load
        consumming = index[0]
        remaining = index[1::]
        return self.addrs[consumming].load(remaining)

    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
    ):
        assert len(index) >= 1
        assert isinstance(index[0], str)
        assert index[0] in self.ty.base.struct.FIELDS

        # Store
        consumming = index[0]
        remaining = index[1::]
        return self.addrs[consumming].store(remaining, source)

    # ──────────── Init From ────────────

    @staticmethod
    @trace_step("ValSOA.init_from", display_entry=True)
    def init_from(type: TyNode, source: ValNode) -> ValSOA:
        from xdsljson.variables.ty.ty_SOA import TySOA

        assert isinstance(type, TySOA)
        assert len(type.n_elements) == 1, "Need to test this before"

        # We need to have a ValBuffer
        if not isinstance(source, ValBuffer):
            source = ValBuffer.init_from(
                TyBuffer(type.get_sizes(), type.base),
                source,
            )

        struct: STRUCTS_TYPE = source.ty.base.struct

        # Init for all attributs
        addrs: dict[str, ValBuffer | ValMemref] = {}
        for attribut in struct.FIELDS.values():
            addrs[attribut.NAME] = source.build_view(attribut.NAME)

        return ValSOA(type, addrs)
