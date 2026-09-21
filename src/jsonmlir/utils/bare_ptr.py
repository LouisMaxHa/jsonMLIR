"""Build a memref from a raw pointer (!llvm.ptr).

The LLVM memref descriptor (ptr, aligned ptr, offset, sizes, and strides) is
built explicitly and then converted to a memref through
``builtin.unrealized_conversion_cast``. This cast is removed by
``finalize-memref-to-llvm`` + ``reconcile-unrealized-casts`` in the pipeline.
"""

from __future__ import annotations

from mlir.dialects import llvm
from mlir.dialects.builtin import UnrealizedConversionCastOp
from mlir.ir import (
    IntegerAttr,
    IntegerType,
    MemRefType,
    ShapedType,
    Type,
    Value,
)


def bare_ptr_to_memref(
    ptr: Value,
    memref_type: MemRefType,
) -> Value:
    """Convert ``!llvm.ptr`` to ``memref<...>`` through an explicit descriptor."""
    shape = list(memref_type.shape)
    rank = len(shape)
    dyn = ShapedType.get_dynamic_size()
    i64 = IntegerType.get_signless(64)

    if rank == 0:
        desc_ty = Type.parse("!llvm.struct<(ptr, ptr, i64)>")
    else:
        desc_ty = Type.parse(
            f"!llvm.struct<(ptr, ptr, i64, array<{rank} x i64>, array<{rank} x i64>)>"
        )

    def c64(value: int) -> Value:
        return llvm.ConstantOp(i64, IntegerAttr.get(i64, value)).result

    # Contiguous row-major strides. A dynamic dimension is allowed only in the
    # outermost position; otherwise the strides could not be calculated.
    strides = [1] * rank
    acc = 1
    for axis in reversed(range(rank)):
        strides[axis] = acc
        if shape[axis] == dyn:
            assert axis == 0, (
                "bare_ptr_to_memref: only the outermost dimension "
                f"may be dynamic ({memref_type})"
            )
        else:
            acc *= shape[axis]

    desc = llvm.UndefOp(desc_ty).result
    desc = llvm.InsertValueOp(desc, ptr, [0]).result
    desc = llvm.InsertValueOp(desc, ptr, [1]).result
    desc = llvm.InsertValueOp(desc, c64(0), [2]).result
    for axis in range(rank):
        # The size of a dynamic dimension is unknown here; load/store lowering
        # does not use it, only the strides.
        size = shape[axis] if shape[axis] != dyn else 0
        desc = llvm.InsertValueOp(desc, c64(size), [3, axis]).result
        desc = llvm.InsertValueOp(desc, c64(strides[axis]), [4, axis]).result

    cast = UnrealizedConversionCastOp([memref_type], [desc])
    return cast.results[0]
