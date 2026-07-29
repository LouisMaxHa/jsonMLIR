from __future__ import annotations

from collections.abc import Sequence
from sqlite3 import NotSupportedError

from mlir.dialects import arith, memref
from mlir.ir import MemRefType, ShapedType, Value

from jsonmlir.trace import trace_step
from jsonmlir.utils.ssa_check import all_ssavalues
from jsonmlir.utils.ssa_dim import dimensions_to_ssa
from jsonmlir.utils.ssa_val import idx_to_ssavalues
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode


class ValMemref(ValNode[TyMemref]):
    addr: Value[MemRefType]

    # ──────────── Init ────────────
    # Problème avec les structs, j'ai du memref<5xmemref<8xi8>>
    def __init__(self, ty: TyMemref, addr: Value[MemRefType]):
        ssa_type = addr.type
        assert isinstance(ssa_type, MemRefType), f"Got {type(addr)}"
        ty_shape = list(ty.get_type().shape)
        ssa_shape = list(ssa_type.shape)
        assert ty_shape == ssa_shape , (
            f"Ty shape {ty_shape} donc match given SSA shape {ssa_shape}".replace(
                str(ShapedType.get_dynamic_size()), "DYNAMIC_INDEX"
            )
        )

        self.addr = addr
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValMemref(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValMemref.init_from", display_entry=True)
    def init_from(type: TyNode, source: ValNode) -> ValMemref:
        assert isinstance(type, TyMemref)

        match source.get_ty():
            case TyMemref():
                return ValMemref(type, source.get_SSA([]))
            case TySSA():
                return ValMemref(type, source.get_SSA([]))
            case _:
                raise NotSupportedError

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
    ) -> ValNode:
        from jsonmlir.variables.factory import Factory

        if index == []:
            return self

        # Split index
        consuming = index[: len(self.ty.dimensions)]
        remaining = index[len(self.ty.dimensions) :]
        assert all_ssavalues(consuming)

        # Load
        if isinstance(self.ty.base, TyStruct):
            assert len(self.ty.dimensions) == 1, "Array of struct supported for only 1D"
            struct_size = self.ty.base.struct.SIZE
            # ViewOp (pas subview) : conserve un layout identité, requis ensuite
            # par les memref.view de champs de struct.
            offset = arith.MulIOp(
                idx_to_ssavalues(consuming[0]),
                idx_to_ssavalues(struct_size),
            ).result

            result_ssa = memref.ViewOp(
                self.ty.base.get_type(),
                self.addr,
                offset,
                [],
            ).result
        else:
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
        source: ValNode,
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

