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
            # ptr<mdspan<i64>> : le MdSpan est passé par adresse (ABI i64).
            ("spanRef", TyPtr(TyMdspan(dims=None, base=TyScalar(Scalar.i64)))),
        ],
        [
            # mdspan = *spanRef
            Set(Var(name="mdspan"), Var("spanRef", ["*"]),),

            Set(Var(name="i", type="i32"), Const(0, "i32")),
            While(
                Binary("<", Var("i"), Var("mdspan", ["size"])),
                [
                    # mdspan[i] += 1
                    Set(
                        Var("mdspan", [Var("i")]),
                        Binary("+", Var("mdspan", [Var("i")]), Const(1, "i64")),
                    ),
                    # i += 1
                    Set(
                        Var("i"),
                        Binary("+", Var("i"), Const(1, "i32")),
                    ),
                ],
            ),

            # return span->size
            Var("mdspan", ["size"]),
        ],
    )
])

compiler(module, [__file__, "--link"] + sys.argv[1:])
