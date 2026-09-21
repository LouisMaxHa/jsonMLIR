from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mlir.dialects import memref

from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_scalar import ValScalar
from jsonmlir.variables.val.val_struct import ValStruct

# One handler per struct: (operator, lhs, rhs) -> result value.
StructMethod = Callable[[OperatorOp, ValNode[Any], ValNode[Any]], ValNode[Any]]

REGISTER_METHODES: dict[str, StructMethod] = {}


def struct_method(struct_name: str) -> Callable[[StructMethod], StructMethod]:
    """Custom operator implementation for structure"""

    def register(fn: StructMethod) -> StructMethod:
        REGISTER_METHODES[struct_name] = fn
        return fn
    return register


def call_structure_method(
    struct_name: str, ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]
) -> ValNode[Any]:
    handler = REGISTER_METHODES.get(struct_name)
    if handler is None:
        raise NotImplementedError(
            f"Struct {struct_name!r} does not implement operator {ope.value!r}"
        )
    return handler(ope, lhs, rhs)


# ──────────── Tools ────────────

def alloc_struct(ty: TyStruct) -> ValStruct:
    """Alloc new struct"""
    op = memref.AllocOp(ty.get_memref_type(), [], [])
    return ValStruct(ty, op.memref)


def elementwise(
    ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]
):
    """Apply operator on structure element wise on based on a scalar"""
    if isinstance(lhs, ValStruct):
        if isinstance(rhs, ValStruct):
            return attributwise(ope, lhs, rhs)
        if isinstance(rhs, ValScalar):
            return attribut_to_scalar(ope, lhs, rhs)

    raise ValueError("elementwise not supported on theses types.")

def attribut_to_scalar(
    ope: OperatorOp, lhs: ValStruct, rhs: ValScalar
) -> ValStruct:
    """Apply a scalar operation to each structure field."""
    from jsonmlir.operations.op_binary import generate_bin_op

    result = alloc_struct(lhs.ty)
    for field_name in lhs.ty.struct.fields:
        left = lhs.load([field_name])
        result.store([field_name], generate_bin_op(ope, left, rhs))
    return result

def attributwise(
    ope: OperatorOp, lhs: ValStruct, rhs: ValStruct
) -> ValStruct:
    """Apply a scalar operation field by field."""
    from jsonmlir.operations.op_binary import generate_bin_op
    assert lhs.ty.name == rhs.ty.name, (
        f"cannot combine {lhs.ty.name!r} with {rhs.ty.name!r}"
    )

    result = alloc_struct(lhs.ty)
    for field_name in lhs.ty.struct.fields:
        left = lhs.load([field_name])
        right = rhs.load([field_name])
        result.store([field_name], generate_bin_op(ope, left, right))
    return result


# ──────────── Methodes ────────────
@struct_method("Real3")
def _real3_operator(
    ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]
) -> ValNode[Any]:
    return elementwise(ope, lhs, rhs)
