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
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_mdspan import TyMdspan
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_struct import TyStruct


REAL2_SIZE = 16


module = Module([
    # Real2 is an inline C++ object: x at byte 0 and y at byte 8.
    DefineStruct(
        "Real2",
        REAL2_SIZE,
        [
            ("x", "f64", 0, 8),
            ("y", "f64", 8, 8),
        ],
    ),
    Function(
        "lib_main",
        [
            (
                "coordinates",
                # The descriptor contains {data, cell_count, nodes_per_cell}.
                TyPtr(
                    TyMdspan(
                        (None, None),
                        TyStruct("Real2"),
                        index_type=Scalar.i32,
                    )
                ),
            ),
            ("cell", TyScalar(Scalar.idx)),
            ("node", TyScalar(Scalar.idx)),
        ],
        [
            Set(Var("coordinates", ["*", Var("cell"), Var("node"), "x"]), Const(10.0)),
            Set(Var("coordinates", ["*", Var("cell"), Var("node"), "y"]), Const(11.0)),
        ],
    ),
])


compiler(module, [__file__, "--link"] + sys.argv[1:])
