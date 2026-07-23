from __future__ import annotations

from mlir.dialects.arith import ConstantOp, IndexCastOp
from mlir.ir import (
    FloatAttr,
    IndexType,
    InsertionPoint,
    IntegerAttr,
    IntegerType,
    Value,
)

from xdsljson.utils.block_entry import function_entry_block
from xdsljson.utils.enum_scalars import Scalar, ScalarFamily

const_heap: dict[tuple[int | float, str], list[Value]] = {}

# TODO: Clear variable end of function


def ensure_index(value: Value, ip: InsertionPoint) -> Value:
    """Cast un entier vers ``index`` si besoin (requis par memref.load/store)."""
    if isinstance(value.type, IndexType):
        return value
    if isinstance(value.type, IntegerType):
        return IndexCastOp(IndexType.get(), value, ip=ip).result
    raise TypeError(f"Impossible de caster {value.type} vers index")


def idx_to_ssavalues(value: int | Value, ip: InsertionPoint) -> Value:
    if isinstance(value, Value):
        return ensure_index(value, ip)
    return val_to_SSAValue(value, Scalar.idx, ip)


def val_to_SSAValues(
    value: int | float, type: Scalar, ip: InsertionPoint
) -> list[Value]:
    key = (value, str(type.get_type()))

    if key not in const_heap.keys():
        # Create const
        mlir_type = type.get_type()
        match type.get_kind():
            case ScalarFamily.float:
                attr = FloatAttr.get(mlir_type, float(value))

            case ScalarFamily.int | ScalarFamily.idx:
                attr = IntegerAttr.get(mlir_type, int(value))

        # Insert it at the start of the enclosing function's entry block
        entry_block = function_entry_block(ip.block)
        op = ConstantOp(
            mlir_type, attr, ip=InsertionPoint.at_block_begin(entry_block)
        )
        const_heap[key] = list(op.results)

    return const_heap[key]


def val_to_SSAValue(value: int | float, type: Scalar, ip: InsertionPoint) -> Value:
    return val_to_SSAValues(value, type, ip)[0]
