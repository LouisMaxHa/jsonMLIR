from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any, Literal

from pydantic import Field

from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_comment import CommentOp
from jsonmlir.operations.op_define_function import DefineFunctionOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_function import FunctionOp
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import functions_registry, structs_registry
from jsonmlir.variables.val.val import ValNode

# Struct declaration, function signature, or function body.
ModuleStatement = Annotated[
    DefineStructOp | DefineFunctionOp | FunctionOp | CommentOp,
    Field(discriminator="op"),
]


class ModuleJsonOp(OpNode):
    """Root operation that contains struct declaration, function declaration, function implementation and comments.


    Example:

    .. code-block:: python

       Module([
        Comment("My first module using jsonMlir!"),
        DefineStruct("coordinate", 16, [("x", "f64", 0, 8), ("y", "f64", 8, 8)]),
        DefineFunction("sum", [TyStruct("coordinate")], "f64")
        Function(
            "sum", [("coo", TyStruct("coordinate")], [
                Binary("+",
                    Var("coo", ["x"]),
                    Var("coo", ["y"])
                )
            ]
        )
       ])
    """

    op: Literal["module"] = "module"
    body: Sequence[ModuleStatement] = ()

    @trace_step("ModuleJsonOp")
    def codegen(self) -> Sequence[ValNode[Any]]:
        structs_registry.clear()
        functions_registry.clear()

        # First pass: register all function declarations before generating
        # bodies, allowing calls in any order.
        for item in self.body:
            if isinstance(item, DefineFunctionOp):
                item.codegen()

        # Main pass: generate the remaining items (structs, function bodies).
        for item in self.body:
            if not isinstance(item, DefineFunctionOp):
                item.codegen()

        return []
