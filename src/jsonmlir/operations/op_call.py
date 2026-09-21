from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from mlir.dialects.func import CallOp as MLIRCallOp
from mlir.ir import Value

from jsonmlir.operations.codegen import OpNode
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.memory import functions_registry
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class CallOp(OpNode):
    """Call a function declared with :class:`DefineFunctionOp`.

    Return types and argument validation are resolved from the global function
    registry. You may need to use `extern C` for the function definition.

    Example:

    .. code-block:: python

       Call("add", [Const(1), Const(2)])
    """

    op: Literal["call"] = "call"
    name: str
    args: Sequence[BaseValue] = ()

    @trace_step("CallOp: {self.name}")
    def codegen(self) -> Sequence[ValNode[Any]]:
        sig = functions_registry.get(self.name)
        if sig is None:
            raise ValueError(
                f"Function '{self.name}' is not declared. "
                "Use DefineFunction in the module before calling it."
            )

        # Evaluate arguments.
        arg_ssas: list[Value] = []
        arg_vals: list[ValNode[Any]] = []
        for arg in self.args:
            vals = arg.codegen()
            arg_vals.extend(vals)
            for val in vals:
                arg_ssas.append(val.get_SSA())

        # Check the argument count.
        if len(arg_ssas) != len(sig.args):
            raise TypeError(
                f"Function '{self.name}' expects {len(sig.args)} argument(s), "
                f"but received {len(arg_ssas)}."
            )

        # Check argument types.
        for i, (val, (_arg_name, expected_ty)) in enumerate(zip(arg_vals, sig.args)):
            actual_type = val.get_type()
            expected_type = expected_ty.get_type()
            if actual_type != expected_type:
                raise TypeError(
                    f"Argument {i} of '{self.name}': "
                    f"expected type {expected_type}, received {actual_type}."
                )

        # Get return types from the registry.
        mlir_return_types = [ty.get_type() for ty in sig.return_types]

        call_op = MLIRCallOp(mlir_return_types, self.name, arg_ssas)

        return [ValSSA(res) for res in call_op.results]
