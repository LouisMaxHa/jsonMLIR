import sys

from jsonmlir.operations.dsl import (
    Function,
    Module,
    Unary,
    Var,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_scalar import TyScalar

module = Module([
    Function(
        "test_neg_float",
        [("x", TyScalar(Scalar.f64))],
        [
            Unary("-f", Var("x")),
        ],
    ),
    Function(
        "test_neg_int",
        [("x", TyScalar(Scalar.i64))],
        [
            Unary("-", Var("x")),
        ],
    ),
    Function(
        "test_neg_bool",
        [("x", TyScalar(Scalar.i1))],
        [
            Unary("!", Var("x")),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
