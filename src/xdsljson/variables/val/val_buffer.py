from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import arith, memref
from mlir.ir import (
    InsertionPoint,
    MemRefType,
    ShapedType,
    StridedLayoutAttr,
    Value,
)

from xdsljson.trace import trace_step
from xdsljson.utils import ssa_val
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.utils.ssa_dim import dimensions_to_ssa
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.ty.ty_buffer import TyBuffer
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_memref import ValMemref
from xdsljson.variables.val.val_SSA import ValSSA


class ValBuffer(ValNode):
    addr: Value
    ty: TyBuffer

    # ──────────── Init ────────────
    def __init__(
        self, ty: TyBuffer, addr: Value
    ):
        assert addr.type == ty.get_type(), f"addr SSAValue type {addr.type} \
            does not match expected {ty.get_type()}"

        self.addr = addr
        self.ty = ty

        assert len(self.ty.dimensions) >= 1

    def __repr__(self) -> str:
        return f"ValBuffer(addr, {self.ty!r})"

    @staticmethod
    @trace_step("ValBuffer.init_from", display_entry=True)
    def init_from(
        type: TyNode, source: ValNode, ip: InsertionPoint
    ) -> ValBuffer:
        assert isinstance(type, TyBuffer)
        assert isinstance(source, (ValMemref, ValSSA))
        return ValBuffer(type, source.get_SSA([], ip))

    # ──────────── Getter ────────────
    def get_ty(self) -> TyBuffer:
        return self.ty

    def get_type(self) -> MemRefType:
        return self.ty.get_type()

    def get_base(self) -> TyNode:
        return self.ty.base

    def get_dim(self, ip: InsertionPoint) -> Sequence[Value]:
        return dimensions_to_ssa(
            self.ty.dimensions,
            self.addr,
            ip
        )

    def _get_SSA(self, ip: InsertionPoint) -> Value:
        return self.addr

    # ──────────── Load ────────────
    @trace_step("{repr(self)}.load")
    def _load(
        self,
        index: Sequence[str | Value],
        ip: InsertionPoint,
    ) -> ValNode:
        assert index == []
        return self

    # ──────────── Store ────────────
    @trace_step("{repr(self)}.store")
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
        ip: InsertionPoint,
    ) -> None:
        raise NotImplementedError


    # ──────────── n_elements ────────────
    """Nombre d'éléments struct = taille buffer / taille struct (octets)."""
    def get_size(self, ip: InsertionPoint) -> Value | int:
        assert len(self.ty.dimensions) >= 1
        struct_size = self.ty.base.struct.SIZE

        # Static size
        n_bytes = self.ty.get_bytes_size()
        if n_bytes is not None:
            assert n_bytes % struct_size == 0
            n_elements =  n_bytes // struct_size
            return n_elements


        # TODO: multiples dim
        assert len(self.ty.dimensions) == 1, "TODO: Only supported for one element"

        # Size (bytes)
        n_bytes_ssa = memref.DimOp(
            self.get_SSA([], ip),
            ssa_val.val_to_SSAValue(0, Scalar.idx, ip),
            ip=ip,
        ).result

        # Size (elements)
        struct_size_ssa = ssa_val.val_to_SSAValue(struct_size, Scalar.idx, ip)
        div_op = arith.DivUIOp(n_bytes_ssa, struct_size_ssa, ip=ip)
        return div_op.result


    def build_view(
        self,
        field_name: str,
        ip: InsertionPoint,
    ) -> ValMemref | ValBuffer:
        from xdsljson.variables.factory import Factory

        dynamic = ShapedType.get_dynamic_size()

        # Load infos
        struct = self.ty.base.struct
        field = struct.FIELDS[field_name]
        field_info = struct.FIELDS[field_name]
        field_type = field_info.TYPE.get_type()
        row_count = self.get_size(ip)
        assert struct.SIZE % field.SIZE == 0


        # ──────────── Get dimensions
        # Offset
        offset_ssa = ssa_val.val_to_SSAValue(field.OFFSET, Scalar.idx, ip)

        # Size after flatten
        row_count = self.get_size(ip)
        stride_size = struct.SIZE // field.SIZE
        if isinstance(row_count, int):
            flat_size = row_count * stride_size
            flat_size_ssa = []
            resulting_size = row_count

        else:
            flat_size = dynamic
            resulting_size = dynamic
            stride_ssa = ssa_val.val_to_SSAValue(stride_size, Scalar.idx, ip)
            flat_size_op = arith.MulIOp(row_count, stride_ssa, ip=ip)
            flat_size_ssa = [flat_size_op.result]

        # ──────────── Flatten

        view_op = memref.ViewOp(
            MemRefType.get([flat_size], field_type),
            self.get_SSA([], ip),
            offset_ssa,
            flat_size_ssa,
            ip=ip,
        )
        flat_view = view_op.result

        # ──────────── Add strides
        if isinstance(row_count, int):
            cast_sizes: list[Value] = []
            static_sizes = [row_count]
        else:
            cast_sizes = [row_count]
            static_sizes = [dynamic]

        cast_op = memref.ReinterpretCastOp(
            MemRefType.get(
                [resulting_size],
                field_type,
                StridedLayoutAttr.get(0, [stride_size]),
            ),
            flat_view,
            [],           # offsets (dynamiques)
            cast_sizes,   # sizes (dynamiques)
            [],           # strides (dynamiques)
            static_offsets=[0],
            static_sizes=static_sizes,
            static_strides=[stride_size],
            ip=ip,
        )

        dimension = row_count if isinstance(row_count, int) else None
        return Factory.generic_memref(
            [dimension],
            field_info.TYPE,
            cast_op.result
        )
