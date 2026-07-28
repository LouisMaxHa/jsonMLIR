from __future__ import annotations

from jsonmlir.operations.dsl import (
    Binary,
    Call,
    Cond,
    Const,
    DefineFunction,
    DefineStruct,
    Function,
    Module,
    Math,
    Print,
    Set,
    Var,
    While,
    Alloc
)
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_cond import CondOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_define_function import DefineFunctionOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_function import FunctionOp
from jsonmlir.operations.op_module import ModuleJsonOp
from jsonmlir.operations.op_print import PrintOp
from jsonmlir.operations.op_set import SetOp
from jsonmlir.operations.op_var import VarOp
from jsonmlir.operations.op_math import MathOp
from jsonmlir.operations.op_while import WhileOp
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar

__all__ = [
    "Binary",
    "BinaryOp",
    "Call",
    "CallOp",
    "Cond",
    "CondOp",
    "Const",
    "ConstOp",
    "DefineFunction",
    "DefineFunctionOp",
    "DefineStruct",
    "DefineStructOp",
    "Function",
    "FunctionOp",
    "MathOp",
    "Module",
    "ModuleJsonOp",
    "Print",
    "PrintOp",
    "Scalar",
    "Set",
    "SetOp",
    "TyScalar",
    "TyMemref",
    "TyPtr",
    "Var",
    "VarOp",
    "While",
    "WhileOp",
    "Alloc",
]
