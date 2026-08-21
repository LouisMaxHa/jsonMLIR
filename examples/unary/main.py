import sys

from jsonmlir.operations import (
    Binary,
    Function,
    Module,
    Scalar,
    Set,
    TyScalar,
    Unary,
    Var,
)
from jsonmlir.pipeline.compiler import compiler

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
