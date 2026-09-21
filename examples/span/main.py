import sys

from jsonmlir.operations.dsl import (
    Binary,
    Const,
    Function,
    Module,
    Set,
    Var,
    While,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_mdspan import TyMdspan
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar

module = Module([
    Function(
        "lib_main",
        [
            # ptr<span<i64>> : le MdSpan est passé par adresse (ABI i64).
            ("spanRef", TyPtr(TyMdspan(dims=None, base=TyScalar(Scalar.i64)))),
        ],
        [
            # span = *spanRef
            Set(Var(name="span"), Var("spanRef", ["*"]),),

            Set(Var(name="i", type="i64"), Const(0, "i64")),
            While(
                Binary("<", Var("i"), Var("span", ["size"])),
                [
                    # span[i] += 1
                    Set(
                        Var("span", [Var("i")]),
                        Binary("+", Var("span", [Var("i")]), Const(1, "i64")),
                    ),
                    # i += 1
                    Set(
                        Var("i"),
                        Binary("+", Var("i"), Const(1, "i64")),
                    ),
                ],
            ),

            # return span->size
            Var("span", ["size"]),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
