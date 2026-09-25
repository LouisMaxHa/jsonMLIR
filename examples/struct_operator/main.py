import sys

from jsonmlir.operations.dsl import (Binary, DefineStruct, Function, Module,
                                     Var)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.variables.ty.ty_struct import TyStruct

module = Module([
    DefineStruct("Real3", 24, [
        ("x", "f64", 0, 8),
        ("y", "f64", 8, 8),
        ("z", "f64", 16, 8),
    ]),

# v1 + v2: delegated to the Real3 handler registered in struct_method.py.
    Function(
        "lib_main",
        [("v1", TyStruct("Real3")), ("v2", TyStruct("Real3"))],
        [
            Binary("+f", Var("v1"), Var("v2")),
        ],
    ),
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
