from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mlir.dialects import func
from mlir.ir import FunctionType, InsertionPoint, TypeAttr, UnitAttr

from xdsljson.operations.base import BaseValue
from xdsljson.operations.block import codegenBlock
from xdsljson.operations.codegen import OpNode
from xdsljson.trace import trace_step
from xdsljson.utils.ssa_val import const_heap
from xdsljson.variables.factory import Factory
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode
from xdsljson.variables.val.val_SSA import ValSSA

availables_functions = {}
class FunctionOp(OpNode):
    op: Literal["function"] = "function"
    name: str
    args: Sequence[tuple[str, TyNode]] = ()
    body: Sequence[BaseValue] = ()

    @trace_step("FunctionOp: {self.name}")
    def codegen(self) -> Sequence[ValNode]:
        variables_heap.clear()
        const_heap.clear()

        # Create function
        input_types = [arg.get_type() for _name, arg in self.args]
        function = func.FuncOp(
            self.name,
            FunctionType.get(input_types, []),  # Output (automatic)
        )
        function.attributes["llvm.emit_c_interface"] = UnitAttr.get()
        entry_block = function.add_entry_block()

        # Init variable
        with InsertionPoint(entry_block):
            with trace_step("Init args"):
                for arg_ssa, (arg_name, arg_type) in zip(
                    entry_block.arguments,
                    self.args
                ):
                    val_arg = ValSSA(arg_ssa)

                    variables_heap[arg_name] = Factory.from_val(
                        arg_type,
                        val_arg,
                    )

        # Block codegen
        body_block, return_values = codegenBlock(self.body, entry_block)

        # Block return
        with InsertionPoint(body_block):
            return_ssas = [a.get_SSA([]) for a in return_values]
            func.ReturnOp(return_ssas)

        # Update function type with the inferred return types
        function.attributes["function_type"] = TypeAttr.get(
            FunctionType.get(input_types, [v.type for v in return_ssas])
        )

        # Return
        return []
