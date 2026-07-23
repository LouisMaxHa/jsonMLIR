"""Conversion des dimensions statiques/dynamiques en SSA Values."""

from __future__ import annotations

from collections.abc import Sequence

from mlir.dialects.memref import DimOp
from mlir.ir import InsertionPoint, Value

from xdsljson.utils import ssa_val
from xdsljson.utils.enum_scalars import Scalar


def dimensions_to_ssa(
    dimensions: Sequence[int | None],
    ref: Value,
    ip: InsertionPoint,
) -> Sequence[Value]:
    """int -> constante index ; None -> memref.dim sur ``ref``."""
    result: list[Value] = []
    for axis, dim in enumerate(dimensions):
        match dim:
            case None:
                axis_ssa = ssa_val.val_to_SSAValue(axis, Scalar.idx, ip)
                op = DimOp(ref, axis_ssa, ip=ip)
                result.append(op.result)

            case int():
                result.append(ssa_val.val_to_SSAValue(dim, Scalar.idx, ip))
    return result


def index_to_ssa(
    index: Sequence[str | Value | int], ip: InsertionPoint
) -> Sequence[str | Value]:
    result: list[str | Value] = []
    for val in index:
        if isinstance(val, str):
            result.append(val)
        elif isinstance(val, Value):
            result.append(ssa_val.ensure_index(val, ip))
        else:
            result.append(ssa_val.val_to_SSAValue(val, Scalar.idx, ip))
    return result
