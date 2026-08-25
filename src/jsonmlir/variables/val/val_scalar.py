from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import memref
from mlir.ir import MemRefType, Value

from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.val.val import ValNode, ValNodeAny
from jsonmlir.variables.val.val_SSA import ValSSA


class ValScalar(ValNode[TyScalar]):
    # ──────────── Init ────────────

    def __init__(self, ty: TyScalar, addr: Value):
        expected = MemRefType.get([], ty.get_type())
        assert addr.type == expected, f"\
        addr SSAValue type {getattr(addr, 'type', None)} \
        does not match expected memref type {expected}"

        self.addr = addr
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValScalar(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValScalar.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNodeAny
    ) -> ValScalar:
        assert isinstance(type, TyScalar)
        assert isinstance(source, (ValSSA, ValScalar))

        # Alloc
        op = memref.AllocaOp(MemRefType.get([], type.get_type()), [], [])

        # Create empty val
        val = ValScalar(
            type,
            op.memref
        )

        # Populate val
        val.store([], source)
        return val

    # ──────────── Getter ────────────
    def get_dim(self) -> Sequence[Value]:
        return []

    def _get_SSA(self) -> Value:
        op = memref.LoadOp(self.addr, [])
        return op.result

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNodeAny:
        assert index == []
        return ValSSA(self.get_SSA(index))


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNodeAny,
    ):
        assert index == []
        assert isinstance(source, (ValSSA, ValScalar))
        ssa = source.get_SSA([])

        # Extract ssa value from memref<ssa value>
        if isinstance(ssa.type, MemRefType):
            op = memref.LoadOp(ssa, [])
            ssa = op.result

        # Store
        memref.StoreOp(ssa, self.addr, [])
