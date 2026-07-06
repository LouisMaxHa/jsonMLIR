from __future__ import annotations

from collections.abc import Sequence

from xdsl.builder import Builder
from xdsl.dialects.builtin import MemRefType
from xdsl.dialects.memref import StoreOp, ViewOp
from xdsl.ir import Attribute, SSAValue

from xdsljson.trace import trace_step
from xdsljson.utils import ssa_val
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.ty.ty_struct import TyStruct
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_SSA import ValSSA


class ValStruct(ValNode):
    addr: SSAValue
    ty: TyStruct

    # ──────────── Init ────────────
    def __init__(
        self, ty: TyStruct, addr: SSAValue
    ):
        assert isinstance(addr, SSAValue), f"got {addr}"
        assert ty.get_type() == addr.type, f"{ty.get_type()} == {addr.type}"
        self.addr = addr
        self.ty = ty

    def __repr__(self) -> str:
        return f"ValStruct(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValStruct.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNode, builder: Builder
    ) -> ValStruct:
        assert isinstance(type, TyStruct)
        return ValStruct(
            type,
            source.get_SSA([], builder)
        )


    # ──────────── Getter ────────────
    def get_ty(self) -> TyStruct:
        return self.ty

    def get_type(self) -> Attribute:
        return self.ty.get_type()

    def get_dim(self, builder: Builder) -> Sequence[SSAValue]:
        raise NotImplementedError

    def _get_SSA(self, builder: Builder) -> SSAValue:
        return self.addr

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | SSAValue[Attribute]],
        builder: Builder,
    ) -> ValNode:
        from xdsljson.variables.factory import Factory

        if len(index) == 0:
            return ValSSA(self.addr)

        assert isinstance(index[0], str)

        # Split index
        consuming = index[0]
        remaining = index[1::]

        # Load
        valNode = Factory.from_val(
            self.ty.struct.FIELDS[consuming].TYPE,
            ValSSA(self._get_field(consuming, builder)),
            builder
        )

        # Recurse
        if remaining:
            return valNode.load(remaining, builder)
        return valNode


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | SSAValue[Attribute]],
        source: ValNode,
        builder: Builder,
    ) -> None:
        assert len(index) > 0
        assert isinstance(index[0], str)

        consuming = index[0]
        remaining = index[1::]

        # Recursif
        if remaining:
            self.load([consuming], builder)\
                .store(remaining, source, builder)
            return

        # Store
        op = StoreOp.get(
            source.get_SSA([], builder),
            self._get_field(consuming, builder),
            []
        )
        builder.insert(op)

    # ──────────── size ────────────
    def get_size(self, builder: Builder) -> int:
        return self.ty.struct.SIZE


    def _get_field(
        self,
        field_name: str,
        builder: Builder,
    ) -> SSAValue:

        # Load infos
        struct = self.ty.struct
        field = struct.FIELDS[field_name]
        field_ty = struct.FIELDS[field_name].TYPE
        assert struct.SIZE % field.SIZE == 0, f"{struct.SIZE} % {field.SIZE} == {struct.SIZE % field.SIZE}"


        # Get dimensions
        offset_ssa = ssa_val.val_to_SSAValue(field.OFFSET, Scalar.idx, builder)
        # size_ssa = ssa_val.val_to_SSAValue(1, Scalar.idx, builder)

        # Flatten
        view_op = ViewOp(
            self.get_SSA([], builder),
            offset_ssa,
            [], # [size_ssa],
            MemRefType(
                field_ty.get_type(),
                []
            ),
        )
        builder.insert(view_op)

        return view_op.result


