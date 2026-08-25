import sys

from jsonmlir.operations.dsl import (
    Binary,
    Call,
    Cond,
    DefineFunction,
    Function,
    Module,
    Set,
    Var,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_scalar import TyScalar

module = Module([
    # Déclaration de la signature de max_i64 (entrées + sortie)
    DefineFunction(
        "max_i64",
        [("a", TyScalar(Scalar.i64)), ("b", TyScalar(Scalar.i64))],
        [TyScalar(Scalar.i64)],
    ),

    # Corps de max_i64 : renvoie le plus grand des deux entiers
    Function(
        "max_i64",
        [("a", TyScalar(Scalar.i64)), ("b", TyScalar(Scalar.i64))],
        [
            Set(Var(name="result", type="i64"), Var("a")),
            Cond(
                cond=Binary(">", Var("b"), Var("a")),
                thenBlock=[Set(Var("result"), Var("b"))],
            ),
            Var("result"),
        ],
    ),

    # Déclaration de la signature de lib_main
    DefineFunction(
        "lib_main",
        [("x", TyScalar(Scalar.i64)), ("y", TyScalar(Scalar.i64))],
        [TyScalar(Scalar.i64)],
    ),

    # Corps de lib_main : appelle max_i64 et renvoie son résultat
    Function(
        "lib_main",
        [("x", TyScalar(Scalar.i64)), ("y", TyScalar(Scalar.i64))],
        [
            Call("max_i64", [Var("x"), Var("y")]),
        ],
    ),
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
