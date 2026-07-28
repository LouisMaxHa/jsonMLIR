"""Construction d'un memref à partir d'un pointeur brut (!llvm.ptr).

On construit explicitement le descripteur
memref LLVM (ptr, ptr alignée, offset, tailles, strides) puis on le convertit
en memref via ``builtin.unrealized_conversion_cast``. Ce cast est résorbé par
``finalize-memref-to-llvm`` + ``reconcile-unrealized-casts`` dans le pipeline.
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
    """``!llvm.ptr`` -> ``memref<...>`` via un descripteur LLVM explicite."""
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

    # Strides row-major contigus. Une dimension dynamique n'est admise qu'en
    # position externe : au-delà, les strides seraient incalculables.
    strides = [1] * rank
    acc = 1
    for axis in reversed(range(rank)):
        strides[axis] = acc
        if shape[axis] == dyn:
            assert axis == 0, (
                "bare_ptr_to_memref : seule la dimension la plus externe "
                f"peut être dynamique ({memref_type})"
            )
        else:
            acc *= shape[axis]

    desc = llvm.UndefOp(desc_ty).result
    desc = llvm.InsertValueOp(desc, ptr, [0]).result
    desc = llvm.InsertValueOp(desc, ptr, [1]).result
    desc = llvm.InsertValueOp(desc, c64(0), [2]).result
    for axis in range(rank):
        # La taille d'une dimension dynamique n'est pas connue ici ; elle n'est
        # pas utilisée par l'abaissement de load/store (seuls les strides le sont).
        size = shape[axis] if shape[axis] != dyn else 0
        desc = llvm.InsertValueOp(desc, c64(size), [3, axis]).result
        desc = llvm.InsertValueOp(desc, c64(strides[axis]), [4, axis]).result

    cast = UnrealizedConversionCastOp([memref_type], [desc])
    return cast.results[0]
