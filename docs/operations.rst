Operations
==========

jsonMLIR domain specific language
---------------------------------

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
.. autoclass:: jsonmlir.operations.op_if.IfOp
.. autoclass:: jsonmlir.operations.op_call.CallOp
.. autoclass:: jsonmlir.operations.op_math.MathOp
.. autoclass:: jsonmlir.operations.op_comment.CommentOp
.. autoclass:: jsonmlir.operations.op_print.PrintOp
.. autoclass:: jsonmlir.operations.op_not_supported.NotSupportedOp