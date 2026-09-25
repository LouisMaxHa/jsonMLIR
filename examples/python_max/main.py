import sys

from jsonmlir.operations.dsl import (Binary, Call, DefineFunction, Function,
                                     If, Module, Set, Var)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_scalar import TyScalar

module = Module([
# Declare the max_i64 signature (inputs + output).
    DefineFunction(
        "max_i64",
        [("a", TyScalar(Scalar.i64)), ("b", TyScalar(Scalar.i64))],
        [TyScalar(Scalar.i64)],
    ),

# max_i64 body: return the larger of the two integers.
    Function(
        "max_i64",
        [("a", TyScalar(Scalar.i64)), ("b", TyScalar(Scalar.i64))],
        [
            Set(Var(name="result", type="i64"), Var("a")),
            If(
                cond=Binary(">", Var("b"), Var("a")),
                thenBlock=[Set(Var("result"), Var("b"))],
            ),
            Var("result"),
        ],
    ),

# Declare the lib_main signature.
    DefineFunction(
        "lib_main",
        [("x", TyScalar(Scalar.i64)), ("y", TyScalar(Scalar.i64))],
        [TyScalar(Scalar.i64)],
    ),

# lib_main body: call max_i64 and return its result.
    Function(
        "lib_main",
        [("x", TyScalar(Scalar.i64)), ("y", TyScalar(Scalar.i64))],
        [
            Call("max_i64", [Var("x"), Var("y")]),
        ],
    ),
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
