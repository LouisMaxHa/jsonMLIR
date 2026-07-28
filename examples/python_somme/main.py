import sys

from jsonmlir.operations import (
    Binary,
    Const,
    Function,
    Module,
    Scalar,
    Set,
    TyScalar,
    Var,
    While,
)
from jsonmlir.pipeline.compiler import compiler

module = Module([
    Function(
        "lib_main",
        [("max", TyScalar(Scalar.i64))],
        [
            Set(Var(name="toto", type="i64"), Const(0)),
            Set(Var(name="i",    type="i64"), Const(0)),
            While(
                Binary("<", Var("i"), Var("max")),
                [
                    Set(
                        Var("toto"),
                        Binary("+", Var("toto"), Var("i")),
                    ),
                    Set(
                        Var("i"),
                        Binary("+", Var("i"), Const(1)),
                    ),
                ],
            ),
            Var("toto"),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
