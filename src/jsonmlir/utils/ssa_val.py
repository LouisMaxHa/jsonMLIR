from __future__ import annotations

from typing import cast

from mlir.dialects.arith import ConstantOp, IndexCastOp
from mlir.ir import (
    IndexType,
    InsertionPoint,
    IntegerType,
    Value,
)

from jsonmlir.utils.block_entry import function_entry_block
from jsonmlir.utils.enum_scalars import Scalar

const_heap: dict[tuple[int | float, str], list[Value]] = {}

# TODO: Clear variable end of function

def ensure_index(value: Value) -> Value:
    """Cast an integer to ``index`` when needed (required by memref.load/store)."""
    if isinstance(value.type, IndexType):
        return value
    if isinstance(value.type, IntegerType):
        return IndexCastOp(IndexType.get(), value).result
        raise TypeError(f"Cannot cast {value.type} to index")


def idx_to_ssavalues(value: int | Value) -> Value:
    if isinstance(value, Value):
        return ensure_index(value)
    return val_to_SSAValue(value, Scalar.idx)


def val_to_SSAValues(
    value: int | float, type: Scalar
) -> list[Value]:
    key = (value, str(type.get_type()))

    if key not in const_heap.keys():
        # Create const
        mlir_type = type.get_type()

        # Insert it at the start of the enclosing function's entry block
        current_ip = cast(InsertionPoint, InsertionPoint.current)
        entry_block = function_entry_block(current_ip.block)
        op = ConstantOp(
            mlir_type,
            value,
            ip=InsertionPoint.at_block_begin(entry_block),
        )
        const_heap[key] = list(op.results)

    return const_heap[key]


def val_to_SSAValue(value: int | float, type: Scalar) -> Value:
    return val_to_SSAValues(value, type)[0]
