"""Constructeurs DSL à arguments positionnels, compatibles basedpyright.

Les classes ``*Op`` restent des modèles Pydantic (validation JSON, codegen).
Ce module expose des fonctions factory typées pour l'écriture manuelle en Python.
"""

from __future__ import annotations

from collections.abc import Sequence

from xdsljson.operations.base import BaseValue
from xdsljson.operations.op_alloc import AllocOp
from xdsljson.operations.op_alloca import AllocaOp
from xdsljson.operations.op_binary import BinaryOp
from xdsljson.operations.op_call import CallOp
from xdsljson.operations.op_cond import CondOp
from xdsljson.operations.op_constant import ConstOp
from xdsljson.operations.op_define_function import DefineFunctionOp
from xdsljson.operations.op_define_struct import DefineStructOp
from xdsljson.operations.op_function import FunctionOp
from xdsljson.operations.op_module import ModuleJsonOp, ModuleStatement
from xdsljson.operations.op_operator import OperatorOp
from xdsljson.operations.op_print import PrintOp
from xdsljson.operations.op_set import SetOp
from xdsljson.operations.op_var import VarOp
from xdsljson.operations.op_while import WhileOp
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.memory import FIELD_TYPE
from xdsljson.variables.ty.ty import TyNode, parse_ty

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


def Print(value: BaseValue) -> PrintOp:
    return PrintOp(value=value)
