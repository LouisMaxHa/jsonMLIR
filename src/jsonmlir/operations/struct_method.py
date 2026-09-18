from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from jsonmlir.operations.dsl import Alloc, Binary, Set, Var
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.variables.memory import get_available_varname
from jsonmlir.variables.ty.ty_struct import TyStruct
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_struct import ValStruct

METHODE_REGISTER: dict[
  str,
  Callable[[OperatorOp, ValNode[Any], ValNode[Any]], ValNode[Any]]
] = {}

def call_operator_method(
  struct_name: str, ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]
) -> ValNode[Any]:

  if struct_name in METHODE_REGISTER.keys():
    return METHODE_REGISTER[struct_name](ope, lhs, rhs)

  raise NotImplementedError(f"{struct_name} dont implement operator")


# Ope
def opeAddReal3(ope: OperatorOp, lhs: ValNode[Any], rhs: ValNode[Any]) -> ValNode[Any]:
  # Check struct name is real3
  assert(isinstance(lhs, ValStruct))
  assert(isinstance(rhs, ValStruct))
  assert(lhs.ty.name == "Real3")
  assert(rhs.ty.name == "Real3")

  # Alloc new struct
  tmp_varname = get_available_varname("_tmp")
  Alloc(tmp_varname, TyStruct("Real3")).codegen()

  # Add .x .y .z to this struct
  for attr in ["x", "y", "z"]:
    Set(Var(tmp_varname, [attr]), Binary(op.ope, 
        Var(op.lhs, [attr]),
        Var(op.rhs, [attr])
      )
    )

  # Return the struct
  return []
