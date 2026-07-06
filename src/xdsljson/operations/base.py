from __future__ import annotations

from typing import Annotated

from pydantic import Field

from xdsljson.operations.op_alloc import AllocOp
from xdsljson.operations.op_binary import BinaryOp
from xdsljson.operations.op_call import CallOp
from xdsljson.operations.op_cond import CondOp
from xdsljson.operations.op_constant import ConstOp
from xdsljson.operations.op_define_struct import DefineStructOp
from xdsljson.operations.op_print import PrintOp
from xdsljson.operations.op_set import SetOp
from xdsljson.operations.op_var import VarOp
from xdsljson.operations.op_while import WhileOp
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.var import Var

# Union discriminé de toutes les opérations connues.
BaseValue = Annotated[
    BinaryOp | CallOp | ConstOp | CondOp | VarOp | WhileOp | PrintOp | SetOp | AllocOp,
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
}

# Rebuild pydantic model because of recursive definitions
BinaryOp.model_rebuild(_types_namespace=_types_namespace)
CallOp.model_rebuild(_types_namespace=_types_namespace)
CondOp.model_rebuild(_types_namespace=_types_namespace)
ConstOp.model_rebuild(_types_namespace=_types_namespace)
DefineStructOp.model_rebuild(_types_namespace=_types_namespace)
PrintOp.model_rebuild(_types_namespace=_types_namespace)
SetOp.model_rebuild(_types_namespace=_types_namespace)
VarOp.model_rebuild(_types_namespace=_types_namespace)
WhileOp.model_rebuild(_types_namespace=_types_namespace)
AllocOp.model_rebuild(_types_namespace=_types_namespace)
