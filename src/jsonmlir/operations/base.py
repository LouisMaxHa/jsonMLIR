from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from jsonmlir.operations.op_alloc import AllocOp
from jsonmlir.operations.op_alloca import AllocaOp
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_cond import CondOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_math import MathOp
from jsonmlir.operations.op_print import PrintOp
from jsonmlir.operations.op_set import SetOp
from jsonmlir.operations.op_unary import UnaryOp
from jsonmlir.operations.op_var import VarOp
from jsonmlir.operations.op_while import WhileOp
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.var import Var

# Union discriminé de toutes les opérations connues.
BaseValue = Annotated[
    BinaryOp | CallOp | ConstOp | CondOp | VarOp | WhileOp
    | PrintOp | SetOp | AllocOp | AllocaOp | MathOp | UnaryOp,
    Field(discriminator="op"),
]

_types_namespace = {
    "BaseValue": BaseValue,
    "BinaryOp": BinaryOp,
    "CallOp": CallOp,
    "CondOp": CondOp,
    "ConstOp": ConstOp,
    "DefineStructOp": DefineStructOp,
    "PrintOp": PrintOp,
    "SetOp": SetOp,
    "VarOp": VarOp,
    "WhileOp": WhileOp,
    "ValScalar": Scalar, # TODO: why ?
    "Var": Var, # TODO: why not only VarOp ?
    "AllocOp": AllocOp,
    "AllocaOp": AllocaOp,
    "MathOp": MathOp,
    "UnaryOp": UnaryOp,
}

# Rebuild pydantic model because of recursive definitions
for model in _types_namespace.values():
    if isinstance(model, type) and issubclass(model, BaseModel):
        model.model_rebuild(_types_namespace=_types_namespace)
