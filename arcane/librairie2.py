import sys

from xdsljson.operations import (
    Binary,
    Call,
    Const,
    DefineFunction,
    DefineStruct,
    Function,
    Math,
    Module,
    Scalar,
    Set,
    TyMemref,
    TyPtr,
    TyScalar,
    Var,
)
from xdsljson.operations.dsl import Alloca
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
    DefineStruct(
        "ComputeGeometricValuesView", 80, [
            ("node_coord", TyPtr(TyMemref([None], TyStruct("Real3"))), 0, 16),
            ("cell_cqs", TyPtr(TyMemref([None, 8], TyStruct("Real3"))), 16, 16),
            ("volume", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 32, 16),
            ("old_volume", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 48, 16),
            ("caracteristic_length", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 64, 16),
        ]
    ),
    DefineFunction(
        "normL2",
        [("r1", TyStruct("Real3"))],
        [TyScalar(Scalar.f64)],
    ),
    Function(
        "normL2",[
            ("r1", TyStruct("Real3"))
        ], [Math("sqrt",
                Binary("+f",
                    Binary("*f", Var("r1", ["x"]), Var("r1", ["x"])),
                    Binary("+f",
                        Binary("*f", Var("r1", ["y"]), Var("r1", ["y"])),
                        Binary("*f", Var("r1", ["z"]), Var("r1", ["z"]))
                    )
                )
            )
        ],
    ),
    Function(
        "xdsl_main",[
            ("face_coord", TyMemref([6], TyStruct("Real3"))),
            ("cid", TyScalar(Scalar.i64)),
            ("out_caracteristic_length", TyMemref([100], TyScalar(Scalar.f64))),
        ], [
            Alloca("median1", TyStruct("Real3")),
            Set(Var("median1", ["x"]), Binary("-f", Var("face_coord", [0, "x"]), Var("face_coord", [3, "x"]))),
            Set(Var("median1", ["y"]), Binary("-f", Var("face_coord", [0, "y"]), Var("face_coord", [3, "y"]))),
            Set(Var("median1", ["z"]), Binary("-f", Var("face_coord", [0, "z"]), Var("face_coord", [3, "z"]))),
            Alloca("median2", TyStruct("Real3")),
            Set(Var("median2", ["x"]), Binary("-f", Var("face_coord", [2, "x"]), Var("face_coord", [5, "x"]))),
            Set(Var("median2", ["y"]), Binary("-f", Var("face_coord", [2, "y"]), Var("face_coord", [5, "y"]))),
            Set(Var("median2", ["z"]), Binary("-f", Var("face_coord", [2, "z"]), Var("face_coord", [5, "z"]))),
            Alloca("median3", TyStruct("Real3")),
            Set(Var("median3", ["x"]), Binary("-f", Var("face_coord", [1, "x"]), Var("face_coord", [4, "x"]))),
            Set(Var("median3", ["y"]), Binary("-f", Var("face_coord", [1, "y"]), Var("face_coord", [4, "y"]))),
            Set(Var("median3", ["z"]), Binary("-f", Var("face_coord", [1, "z"]), Var("face_coord", [4, "z"]))),

            Set(Var("d1", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median1")])),
            Set(Var("d2", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median2")])),
            Set(Var("d3", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median3")])),

            Set(Var("dx_numerator", type=TyScalar(Scalar.f64)), Binary("*f", Var("d1"), Binary("*f", Var("d2"), Var("d3")))),
            Set(Var("dx_denominator", type=TyScalar(Scalar.f64)),
                Binary("+f",
                    Binary("*f", Var("d1"), Var("d2")),
                    Binary("+f",
                        Binary("*f", Var("d1"), Var("d3")),
                        Binary("*f", Var("d2"), Var("d3"))
                    )
                )
            ),
            Set(Var("out_caracteristic_length", [Var("cid"), ]), Binary("/f", Var("dx_numerator"), Var("dx_denominator"))),
            Const(0, type=Scalar.i64)
        ],
    )
])

compiler(module, [__file__, "--output-name", "librairie2"] + sys.argv[1:])
