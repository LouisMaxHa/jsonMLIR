from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import memref
from mlir.ir import InsertionPoint, MemRefType, Type, Value

from xdsljson.trace import trace_step
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.ty.ty_scalar import TyScalar
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_SSA import ValSSA


class ValScalar(ValNode):
    addr: Value
    ty: TyScalar

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
        type: TyNode, source: ValNode, ip: InsertionPoint
    ) -> ValScalar:
        assert isinstance(type, TyScalar)
        assert isinstance(source, (ValSSA, ValScalar))

        # Alloc
        op = memref.AllocaOp(MemRefType.get([], type.get_type()), [], [], ip=ip)

        # Create empty val
        val = ValScalar(
            type,
            op.memref
        )

        # Populate val
        val.store([], source, ip)
        return val

    # ──────────── Getter ────────────
    def get_ty(self) -> TyScalar:
        return self.ty

    def get_type(self) -> Type:
        return self.ty.get_type()

    def get_dim(self, ip: InsertionPoint) -> Sequence[Value]:
        return []

    def _get_SSA(self, ip: InsertionPoint) -> Value:
        op = memref.LoadOp(self.addr, [], ip=ip)
        return op.result

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
        ip: InsertionPoint,
    ) -> ValNode:
        assert index == []
        return ValSSA(self.get_SSA(index, ip))


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
        ip: InsertionPoint,
    ):
        assert index == []
        assert isinstance(source, (ValSSA, ValScalar))
        ssa = source.get_SSA([], ip)

        # Extract ssa value from memref<ssa value>
        if isinstance(ssa.type, MemRefType):
            op = memref.LoadOp(ssa, [], ip=ip)
            ssa = op.result

        # Store
        memref.StoreOp(ssa, self.addr, [], ip=ip)
