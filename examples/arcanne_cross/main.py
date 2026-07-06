import sys

from xdsljson.operations import (
    Alloc,
    Binary,
    DefineStruct,
    Function,
    Module,
    Set,
    TyPtr,
    Var,
)
from xdsljson.pipeline.compiler import compiler
from xdsljson.variables.ty.ty_struct import TyStruct

module = Module([
    DefineStruct(
        "Real3", 24, [
            ("x", "f64", 0, 8),
            ("y", "f64", 8, 8),
            ("z", "f64", 16, 8),
        ]
    ),

    Function(
        "xdsl_main",
        [
            ("v1", TyPtr(TyStruct("Real3"))),
            ("v2", TyPtr(TyStruct("Real3"))),
        ],
        [
            Alloc("v3", TyStruct("Real3")),
            Set(Var("v3", ["x"]),
                Binary("-f",
                    Binary("*f",
                        Var("v1", ["*", "y"]),
                        Var("v2", ["*", "z"])
                    ),
                    Binary("*f",
                        Var("v1", ["*", "z"]),
                        Var("v2", ["*", "y"])
                    )
                )
            ),
            Set(Var("v3", ["y"]),
                Binary("-f",
                    Binary("*f",
                        Var("v2", ["*", "x"]),
                        Var("v1", ["*", "z"])
                    ),
                    Binary("*f",
                        Var("v2", ["*", "z"]),
                        Var("v1", ["*", "x"])
                    )
                )
            ),
            Set(Var("v3", ["z"]),
                Binary("-f",
                    Binary("*f",
                        Var("v1", ["*", "x"]),
                        Var("v2", ["*", "y"])
                    ),
                    Binary("*f",
                        Var("v1", ["*", "y"]),
                        Var("v2", ["*", "x"])
                    )
                )
            ),
            Var("v3")
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
