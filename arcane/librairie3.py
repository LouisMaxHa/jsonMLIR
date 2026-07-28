import sys

# Set(Var("median1", ["x"]), Binary("-f", Var("face_coord", [0, "x"]), Var("face_coord", [3, "x"]))),
# Set(Var("median1", ["y"]), Binary("-f", Var("face_coord", [0, "y"]), Var("face_coord", [3, "y"]))),
# Set(Var("median1", ["z"]), Binary("-f", Var("face_coord", [0, "z"]), Var("face_coord", [3, "z"]))),
def SetReal3(result, v1, ope: str, v2, skip_att_v2=False):
    return [
        Set(Var(result[0], result[1::] + [attribut]), Binary(ope, Var(v1[0], v1[1::] + [attribut]), Var(v2[0], v2[1::] + ([attribut] if not skip_att_v2 else []))))
        for attribut in ["x", "y", "z"]
    ]

def flatten(lst):
    flat_list = []
    for element in lst:
        if isinstance(element, list):
            flat_list.extend(flatten(element))
        else:
            flat_list.append(element)
    return flat_list


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
            ("coord", TyMemref([8], TyStruct("Real3"))),
            ("cid", TyScalar(Scalar.i64)),
            ("out_caracteristic_length", TyMemref([100], TyScalar(Scalar.f64))),
        ], [  # pyright: ignore[reportUnknownArgumentType]
            Alloca("face_coord", TyMemref([6], TyStruct("Real3"))),
            Set(Var("c025", type=TyScalar(Scalar.f64)), Const(0.25, type="f64")),
            *flatten([
                SetReal3(["face_coord", i], ["coord", a], "+f", ["coord", b])
                + SetReal3(["face_coord", i], ["face_coord", i], "+f", ["coord", c])
                + SetReal3(["face_coord", i], ["face_coord", i], "+f", ["coord", d])
                + SetReal3(["face_coord", i], ["face_coord", i], "*f", ["c025"], skip_att_v2=True)

                for i, (a, b, c, d) in enumerate([
                    (0, 3, 2, 1),
                    (0, 4, 7, 3),
                    (0, 1, 5, 4),
                    (4, 5, 6, 7),
                    (1, 2, 6, 5),
                    (2, 3, 7, 6),
                ])
            ]),

            Alloca("median1", TyStruct("Real3")),
            Alloca("median2", TyStruct("Real3")),
            Alloca("median3", TyStruct("Real3")),
            *SetReal3(["median1"], ["face_coord", 0], "-f", ["face_coord", 3]),
            *SetReal3(["median2"], ["face_coord", 2], "-f", ["face_coord", 5]),
            *SetReal3(["median3"], ["face_coord", 1], "-f", ["face_coord", 4]),

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

compiler(module, [__file__, "--output-name", "librairie3"] + sys.argv[1:])
