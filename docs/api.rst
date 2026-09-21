API Reference
=============

Python DSL
----------

The DSL functions are convenience constructors for the operation models. They
normalize shorthand type and operator values, while their API descriptions are
maintained on the corresponding ``*Op`` classes in the source modules.

.. automodule:: jsonmlir.operations.dsl
   :members:

Operation models
----------------

.. autoclass:: jsonmlir.operations.op_module.ModuleJsonOp
.. autoclass:: jsonmlir.operations.op_define_struct.DefineStructOp
.. autoclass:: jsonmlir.operations.op_define_function.DefineFunctionOp
.. autoclass:: jsonmlir.operations.op_alloc.AllocOp
.. autoclass:: jsonmlir.operations.op_alloca.AllocaOp
.. autoclass:: jsonmlir.operations.op_function.FunctionOp
.. autoclass:: jsonmlir.operations.op_var.VarOp
.. autoclass:: jsonmlir.operations.op_constant.ConstOp
.. autoclass:: jsonmlir.operations.op_binary.BinaryOp
.. autoclass:: jsonmlir.operations.op_unary.UnaryOp
.. autoclass:: jsonmlir.operations.op_set.SetOp
.. autoclass:: jsonmlir.operations.op_while.WhileOp
.. autoclass:: jsonmlir.operations.op_cond.IfOp
.. autoclass:: jsonmlir.operations.op_call.CallOp
.. autoclass:: jsonmlir.operations.op_math.MathOp
.. autoclass:: jsonmlir.operations.op_comment.CommentOp
.. autoclass:: jsonmlir.operations.op_print.PrintOp
.. autoclass:: jsonmlir.operations.op_not_supported.NotSupportedOp

Compiler pipeline
-----------------

.. automodule:: jsonmlir.pipeline.compiler
   :members:
   :exclude-members: MLIR_OPT_PASSES, LLVM_OPT_PASSES, MLIR_OPT_LOWER_TO_LLVM

.. automodule:: jsonmlir.pipeline.cli
   :members:

Toolchain commands
------------------

.. automodule:: jsonmlir.pipeline.commands
   :members:

Types and values
----------------

.. automodule:: jsonmlir.variables.ty.ty
   :members:

.. automodule:: jsonmlir.variables.factory
   :members:

.. automodule:: jsonmlir.variables.memory
   :members:
