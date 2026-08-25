from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import memref
from mlir.ir import MemRefType, Value

from jsonmlir.utils import ssa_val
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode, ValNodeAny
from jsonmlir.variables.val.val_SSA import ValSSA


class ValStruct(ValNode[TyStruct]):
    # ──────────── Init ────────────
    def __init__(
        self, ty: TyStruct, addr: Value
    ):
        assert isinstance(addr, Value), f"got {addr}"
        assert ty.get_type() == addr.type, f"{ty.get_type()} == {addr.type}"
        self.addr = addr
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValStruct(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValStruct.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNodeAny
    ) -> ValStruct:
        assert isinstance(type, TyStruct)
        return ValStruct(
            type,
            source.get_SSA([])
        )


    # ──────────── Getter ────────────
    def get_dim(self) -> Sequence[Value]:
        raise NotImplementedError

    def _get_SSA(self) -> Value:
        return self.addr

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNodeAny:
        from jsonmlir.variables.factory import Factory

        if len(index) == 0:
            return ValSSA(self.addr)

        assert isinstance(index[0], str)

        # Split index
        consuming = index[0]
        remaining = index[1::]

        # Load
        valNode = Factory.from_val(
            self.ty.struct.fields[consuming].type,
            ValSSA(self._get_field(consuming)),
        )

        # Recurse
        if remaining:
            return valNode.load(remaining)
        return valNode


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNodeAny,
    ) -> None:
        assert len(index) > 0
        assert isinstance(index[0], str)

        consuming = index[0]
        remaining = index[1::]

        # Recursif
        if remaining:
            self.load([consuming])\
                .store(remaining, source)
            return

        # Store
        memref.StoreOp(
            source.get_SSA([]),
            self._get_field(consuming),
            [],
        )

    # ──────────── size ────────────
    def get_size(self) -> int:
        return self.ty.struct.size


    def _get_field(
        self,
        field_name: str,
    ) -> Value:

        # Load infos
        struct = self.ty.struct
        field = struct.fields[field_name]
        field_ty = struct.fields[field_name].type
        assert struct.size % field.size == 0, f"{struct.size} % {field.size} == {struct.size % field.size}"


        # Get dimensions
        offset_ssa = ssa_val.val_to_SSAValue(field.offset, Scalar.idx)

        # Flatten
        view_op = memref.ViewOp(
            MemRefType.get([], field_ty.get_type()),
            self.get_SSA([]),
            offset_ssa,
            [],
        )

        return view_op.result
