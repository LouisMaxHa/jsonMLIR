from __future__ import annotations

import builtins
from collections.abc import Sequence
from typing import Any

from mlir.dialects import arith
from mlir.ir import MemRefType, Value

from jsonmlir.utils import ssa_val
from jsonmlir.utils.same_types import assert_same_shape
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.ty.ty_mdspan import MDSPAN_SIZE_ATTR_NAME, TyMdspan
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA
from jsonmlir.variables.val.val_struct import ValStruct


class ValMdspan(ValNode[TyMdspan]):
    # ──────────── Init ────────────
    def __init__(self, ty: TyMdspan, addr: Value):
        assert isinstance(addr.type, MemRefType)
        assert_same_shape(ty.get_type().shape, addr.type.shape)

        self.ty = ty
        self.addr = addr

    @staticmethod
    @trace_step("ValMdspan.init_from", display_entry=True)
    def init_from(ty: TyMdspan, source: ValNode[Any]) -> ValMdspan:
        assert isinstance(source, (ValSSA, ValMdspan)), f"Got {source}"
        return ValMdspan(ty, source.get_SSA())

    def __repr__(self) -> str:
        return f"ValMdspan(addr, {self.ty!r})"


    # ──────────── Getter ────────────
    def get_base(self) -> TyNode:
        return self.ty.base

    def get_struct(self) -> ValStruct:
        return ValStruct(self.ty.get_struct(), self.addr)

    def get_dim(self) -> Sequence[Value]:
        """Return a mlir Value containing the dynamic size of the mdspan first dimension
        """
        return [
            ssa_val.ensure_index(self.get_struct().load([
                MDSPAN_SIZE_ATTR_NAME,
            ]).get_SSA())
        ]

    def _get_SSA(self) -> Value:
        return self.addr

    # ──────────── Index ────────────
    def _linear_index(self, index: Sequence[Value]) -> Value:
        n_dims = len(self.ty.dims)
        assert len(index) == n_dims

        match(n_dims):
            # One dimension
            case 1:
                return ssa_val.ensure_index(index[0])

            # Two dimension
            case 2:
                i_first_dim, y_second_dim = index
                n_first_dim = self.get_dim()[0]

                # Row-major index = row * row_size + column.
                return arith.AddIOp(
                    arith.MulIOp(
                        ssa_val.ensure_index(i_first_dim),
                        ssa_val.ensure_index(n_first_dim),
                    ).result,
                    ssa_val.ensure_index(y_second_dim),
                ).result

            # Default
            case _:
                raise ValueError(
                    f"mdspan only support up to 2 dimensions, got {n_dims}"
                )

    def _data_index(self, index: Sequence[Value]) -> list[Value | str]:
        return ["data", "*", self._linear_index(index)]

    # ──────────── Load ────────────
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode[Any]:
        if index == []:
            return self

        match(type(index[0])):
            # str   -> consider struct (.data, .sizeFirstDimension)
            case builtins.str:
                # In 1D, size = sizeFirstDimension
                if index[0] == "size" and len(self.ty.dims) == 1:
                    index = list(index)
                    index[0] = MDSPAN_SIZE_ATTR_NAME

                return self.get_struct().load(index)

            # Value -> load data and apply
            case Value:
                rank = len(self.ty.dims)
                value_index = index[:rank]
                assert all(isinstance(value, Value) for value in value_index)
                return self.get_struct().load(
                    self._data_index(value_index) + list(index[rank:])
                )


    # ──────────── Store ────────────
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode[Any],
    ):
        assert(len(index) > 0)
        match(type(index[0])):
            # str   -> consider struct (.data, .sizeFirstDimension)
            case builtins.str:
                # In 1D, size = sizeFirstDimension
                if index[0] == "size" and len(self.ty.dims) == 1:
                    index = list(index)
                    index[0] = MDSPAN_SIZE_ATTR_NAME

                return self.get_struct().store(index, source)

            # Value -> load data and apply
            case Value:
                rank = len(self.ty.dims)
                value_index = index[:rank]
                assert all(isinstance(value, Value) for value in value_index)
                return self.get_struct().store(
                    self._data_index(value_index) + list(index[rank:]),
                    source,
                )
