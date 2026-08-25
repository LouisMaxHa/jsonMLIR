from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects import arith, memref
from mlir.ir import MemRefType, ShapedType, StridedLayoutAttr, Value

from jsonmlir.utils import ssa_val
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.utils.ssa_dim import dimensions_to_ssa
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_buffer import TyBuffer
from jsonmlir.variables.val.val import ValNode, ValNodeAny
from jsonmlir.variables.val.val_memref import ValMemref
from jsonmlir.variables.val.val_SSA import ValSSA


class ValBuffer(ValNode[TyBuffer]):
    # ``addr`` est inféré depuis ``__init__`` (voir val_SSA.py).

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
        type: TyNode, source: ValNodeAny
    ) -> ValBuffer:
        assert isinstance(type, TyBuffer)
        assert isinstance(source, (ValMemref, ValSSA))
        return ValBuffer(type, source.get_SSA([]))

    # ──────────── Getter ────────────
    def get_base(self) -> TyNode:
        return self.ty.base

    def get_dim(self) -> Sequence[Value]:
        return dimensions_to_ssa(
            self.ty.dimensions,
            self.addr,
        )

    def _get_SSA(self) -> Value:
        return self.addr

    # ──────────── Load ────────────
    @trace_step("{repr(self)}.load")
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNodeAny:
        assert index == []
        return self

    # ──────────── Store ────────────
    @trace_step("{repr(self)}.store")
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNodeAny,
    ) -> None:
        raise NotImplementedError


    # ──────────── n_elements ────────────
    """Nombre d'éléments struct = taille buffer / taille struct (octets)."""
    def get_size(self) -> Value | int:
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
            self.get_SSA([]),
            ssa_val.val_to_SSAValue(0, Scalar.idx),
        ).result

        # Size (elements)
        struct_size_ssa = ssa_val.val_to_SSAValue(struct_size, Scalar.idx)
        div_op = arith.DivUIOp(n_bytes_ssa, struct_size_ssa)
        return div_op.result


    def build_view(
        self,
        field_name: str,
    ) -> ValMemref | ValBuffer:
        from jsonmlir.variables.factory import Factory

        dynamic = ShapedType.get_dynamic_size()

        # Load infos
        struct = self.ty.base.struct
        field = struct.FIELDS[field_name]
        field_info = struct.FIELDS[field_name]
        field_type = field_info.TYPE.get_type()
        row_count = self.get_size()
        assert struct.SIZE % field.SIZE == 0


        # ──────────── Get dimensions
        # Offset
        offset_ssa = ssa_val.val_to_SSAValue(field.OFFSET, Scalar.idx)

        # Size after flatten
        row_count = self.get_size()
        stride_size = struct.SIZE // field.SIZE
        if isinstance(row_count, int):
            flat_size = row_count * stride_size
            flat_size_ssa = []
            resulting_size = row_count

        else:
            flat_size = dynamic
            resulting_size = dynamic
            stride_ssa = ssa_val.val_to_SSAValue(stride_size, Scalar.idx)
            flat_size_op = arith.MulIOp(row_count, stride_ssa)
            flat_size_ssa = [flat_size_op.result]

        # ──────────── Flatten

        view_op = memref.ViewOp(
            MemRefType.get([flat_size], field_type),
            self.get_SSA([]),
            offset_ssa,
            flat_size_ssa,
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
        )

        dimension = row_count if isinstance(row_count, int) else None
        return Factory.generic_memref(
            [dimension],
            field_info.TYPE,
            cast_op.result
        )
