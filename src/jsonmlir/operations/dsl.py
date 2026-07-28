"""Constructeurs DSL à arguments positionnels, compatibles basedpyright.

Les classes ``*Op`` restent des modèles Pydantic (validation JSON, codegen).
Ce module expose des fonctions factory typées pour l'écriture manuelle en Python.
"""

from __future__ import annotations

from collections.abc import Sequence

from jsonmlir.operations.op_math import MathOp, MathOperator

from jsonmlir.operations.base import BaseValue
from jsonmlir.operations.op_alloc import AllocOp
from jsonmlir.operations.op_alloca import AllocaOp
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_cond import CondOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_define_function import DefineFunctionOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_function import FunctionOp
from jsonmlir.operations.op_module import ModuleJsonOp, ModuleStatement
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.operations.op_print import PrintOp
from jsonmlir.operations.op_set import SetOp
from jsonmlir.operations.op_var import VarOp
from jsonmlir.operations.op_while import WhileOp
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import FIELD_TYPE
from jsonmlir.variables.ty.ty import TyNode, parse_ty

FieldSpec = tuple[str, str | TyNode, int, int] | FIELD_TYPE


def _parse_ty(value: str | TyNode) -> TyNode:
    return parse_ty(value) if isinstance(value, str) else value


def _parse_scalar(value: str | Scalar) -> Scalar:
    if isinstance(value, Scalar):
        return value
    return Scalar(value)


def _parse_field(field: FieldSpec) -> FIELD_TYPE:
    if isinstance(field, FIELD_TYPE):
        return field
    name, ty, offset, size = field
    return FIELD_TYPE(name, _parse_ty(ty), offset, size)


def _parse_ope(ope: str | OperatorOp) -> OperatorOp:
    return ope if isinstance(ope, OperatorOp) else OperatorOp(ope)

def _parse_ope_math(ope: str | MathOperator) -> MathOperator:
    return ope if isinstance(ope, MathOperator) else MathOperator(ope)


def Module(body: Sequence[ModuleStatement] = ()) -> ModuleJsonOp:
    return ModuleJsonOp(body=body)


def DefineStruct(
    name: str,
    size: int,
    fields: Sequence[FieldSpec],
) -> DefineStructOp:
    return DefineStructOp(
        name=name,
        size=size,
        fields=[_parse_field(field) for field in fields],
    )


def DefineFunction(
    name: str,
    args: Sequence[tuple[str, TyNode]] = (),
    return_types: Sequence[TyNode] = (),
) -> DefineFunctionOp:
    return DefineFunctionOp(name=name, args=args, return_types=return_types)

def Alloc(
    name: str,
    type: TyNode,
    size: Sequence[int | VarOp] = ()
) -> AllocOp:
    return AllocOp(name=name, type=type, size=size)

def Alloca(
    name: str,
    type: TyNode,
    size: Sequence[int | VarOp] = ()
) -> AllocaOp:
    return AllocaOp(name=name, type=type, size=size)

def Function(
    name: str,
    args: Sequence[tuple[str, TyNode]] = (),
    body: Sequence[BaseValue] = (),
) -> FunctionOp:
    return FunctionOp(name=name, args=args, body=body)


def Var(
    name: str,
    indices: Sequence[int | str | VarOp] = (),
    *,
    type: TyNode | str | None = None,
) -> VarOp:
    return VarOp(
        name=name,
        indices=indices,
        type=_parse_ty(type) if isinstance(type, str) else type,
    )


def Const(
    val: float | int,
    type: str | Scalar = Scalar.i64,
) -> ConstOp:
    return ConstOp(val=val, type=_parse_scalar(type))


def Binary(
    ope: str | OperatorOp,
    lhs: BaseValue,
    rhs: BaseValue,
) -> BinaryOp:
    return BinaryOp(lhs=lhs, rhs=rhs, ope=_parse_ope(ope))


def Set(var: VarOp, val: BinaryOp | ConstOp | VarOp | CallOp) -> SetOp:
    return SetOp(var=var, val=val)


def While(
    cond: BaseValue,
    thenBlock: Sequence[BaseValue],
) -> WhileOp:
    return WhileOp(cond=cond, thenBlock=thenBlock)


def Cond(
    cond: BaseValue,
    thenBlock: Sequence[BaseValue],
    elseBlock: Sequence[BaseValue] | None = None,
) -> CondOp:
    return CondOp(cond=cond, thenBlock=thenBlock, elseBlock=elseBlock)


def Call(
    name: str,
    args: Sequence[BaseValue] = (),
) -> CallOp:
    return CallOp(name=name, args=args)

def Math(
    ope: str | MathOperator,
    value: BaseValue,
) -> MathOp:
    return MathOp(ope=_parse_ope_math(ope), value=value)


def Print(value: BaseValue) -> PrintOp:
    return PrintOp(value=value)
