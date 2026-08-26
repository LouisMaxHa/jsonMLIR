import sys

from jsonmlir.operations.dsl import (
    Binary,
    Function,
    Module,
    Set,
    Unary,
    Var,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_scalar import TyScalar

module = Module([
    Function(
        "lib_main",
        [("x", TyScalar(Scalar.i64)), ("y", TyScalar(Scalar.i64))],
        [
            # x = -x
            Set(Var("x"), Unary("-", Var("x"))),

            # y = !y
            Set(Var("y"), Unary("!", Var("y"))),

            Binary("+", Var("x"), Var("y")),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
