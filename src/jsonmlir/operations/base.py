from __future__ import annotations

from typing import Annotated, get_args

from pydantic import BaseModel, Field

from jsonmlir.operations.op_alloc import AllocOp
from jsonmlir.operations.op_alloca import AllocaOp
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_comment import CommentOp
from jsonmlir.operations.op_const import ConstOp
from jsonmlir.operations.op_if import IfOp
from jsonmlir.operations.op_math import MathOp
from jsonmlir.operations.op_not_supported import NotSupportedOp
from jsonmlir.operations.op_print import PrintOp
from jsonmlir.operations.op_set import SetOp
from jsonmlir.operations.op_unary import UnaryOp
from jsonmlir.operations.op_var import VarOp
from jsonmlir.operations.op_while import WhileOp

# Discriminated union of all known operations.
BaseValue = Annotated[
    BinaryOp | CallOp | ConstOp | IfOp | VarOp | WhileOp | PrintOp | SetOp | AllocOp
    | AllocaOp | MathOp | UnaryOp | NotSupportedOp | CommentOp,
    Field(discriminator="op"),
]

_base_value_union, *_ = get_args(BaseValue)
_base_value_models = tuple(
    model
    for model in get_args(_base_value_union)
    if isinstance(model, type) and issubclass(model, BaseModel)
)
_model_namespace = {
    "BaseValue": BaseValue,
    **{
        model.__name__: model
        for model in _base_value_models
    },
}

# Rebuild pydantic model because of recursive definitions
for model in _base_value_models:
    model.model_rebuild(_types_namespace=_model_namespace)
