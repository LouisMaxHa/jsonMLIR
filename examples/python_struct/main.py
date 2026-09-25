import sys

from jsonmlir.operations.dsl import (
    Binary,
    Const,
    DefineStruct,
    Function,
    Module,
    Set,
    Var,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.variables.ty.ty_struct import TyStruct

module = Module([
    DefineStruct(
        "noeud", 16, [
            ("capacite", "i32", 0, 4),
            ("temperature", "f64", 8, 4)
        ]
    ),

    Function(
        "lib_main",
        [("myStruct", TyStruct("noeud"))],
        [
            Set(Var("myStruct", ["capacite"]),
                Binary("+", Var("myStruct", ["capacite"]), Const(1, "i32"))
            ),
            Set(Var("myStruct", ["temperature"]),
                Binary("+f", Var("myStruct", ["temperature"]), Const(0.1, "f64"))
            ),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
