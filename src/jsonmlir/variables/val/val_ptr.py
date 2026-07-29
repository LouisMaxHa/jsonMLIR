from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import llvm, memref
from mlir.ir import MemRefType, Value

from jsonmlir.trace import trace_step
from jsonmlir.utils.bare_ptr import bare_ptr_to_memref
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_scalar import ValScalar
from jsonmlir.variables.val.val_SSA import ValSSA


class ValPtr(ValNode[TyPtr]):
    addr: Value

    # ──────────── Init ────────────

    def __init__(self, ty: TyPtr, addr: Value):
        expected = MemRefType.get([], ty.get_type())
        assert addr.type == expected, f"\
        addr SSAValue type {getattr(addr, 'type', None)} \
        does not match expected memref type {expected}"

        self.addr = addr
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValPtr(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValPtr.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNode
    ) -> ValPtr:
        assert isinstance(type, TyPtr)
        assert isinstance(source, (ValSSA, ValScalar, ValPtr))

        # Alloc
        op = memref.AllocaOp(MemRefType.get([], type.get_type()), [], [])

        # Create empty addr
        val = ValPtr(
            type,
            op.memref
        )

        # Populate addr
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
    ) -> ValNode:
        from jsonmlir.variables.factory import Factory
        # Return ptr
        if index == []:
            return ValSSA(self.get_SSA(index))

        # Consume index
        consuming = index[0]
        remaining = index[1::]
        assert consuming == "*"

        # i64 -> llvm.ptr
        ssa_i64 = self._get_SSA()
        ssa_ptr_llvm = llvm.IntToPtrOp(
            llvm.PointerType.get(), ssa_i64
        ).result

        # llvm.ptr -> memref (descripteur LLVM explicite)
        ssa_derefed = ValSSA(
            bare_ptr_to_memref(
                ssa_ptr_llvm,
                self.ty.base.get_memref_type(),
            )
        )

        # Convert to val
        val = Factory.from_val(
            self.ty.base,
            ssa_derefed,
        )

        return val.load(remaining)

    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
    ):
        assert index == []
        assert isinstance(source, (ValSSA, ValPtr, ValScalar))
        ssa = source.get_SSA([])

        # Extract ssa value from memref<ssa value>
        if isinstance(ssa.type, MemRefType):
            op = memref.LoadOp(ssa, [])
            ssa = op.result

        # Store
        memref.StoreOp(ssa, self.addr, [])
