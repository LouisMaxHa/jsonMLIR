from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from xdsl.builder import Builder
from xdsl.dialects.builtin import UnitAttr
from xdsl.dialects.func import FuncOp, ReturnOp
from xdsl.rewriter import InsertPoint

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
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        variables_heap.clear()
        const_heap.clear()

        # Create function
        func = FuncOp(self.name, (
            [arg.get_type() for _name, arg in self.args], # Input
            [] # Output (automatic)
        ))
        func.attributes["llvm.emit_c_interface"] = UnitAttr()
        builder.insert(func)

        # Set args name
        for arg_ssa, (arg_name, _arg_type) in zip(
            func.args,
            self.args
        ):
            arg_ssa.name_hint = arg_name + "Arg"

        # Init variable
        inside_function_builder = Builder(InsertPoint.at_end(func.body.block))
        with trace_step("Init args"):
            for arg_ssa, (arg_name, arg_type) in zip(
                func.args,
                self.args
            ):
                val_arg = ValSSA(arg_ssa)

                variables_heap[arg_name] = Factory.from_val(
                    arg_type,
                    val_arg,
                    inside_function_builder
                )

        # Block codegen
        body_block, return_values = codegenBlock(self.body, func.body.block)
        return_types = [
            a.get_SSA([], inside_function_builder)
            for a in return_values
        ]

        # Block return
        body_block.add_op(ReturnOp(*return_types))
        func.update_function_type()

        # Return
        return []
