Quick Start
===========

Installation
------------

The recommended installation uses the repository's Docker wrapper. From the
repository root:

.. code-block:: console

   $ docker build -t jsonmlir .
   $ export PATH="$(pwd)/bin:$PATH"

See ``INSTALL.md`` in the repository for the manual LLVM/MLIR setup.

Python DSL
----------

The ``jsonmlir.operations.dsl`` module contains concise constructors for
building a typed operation tree:

.. code-block:: python

   from jsonmlir.operations.dsl import Binary, Const, Function, Module, Var
   from jsonmlir.variables.ty.ty_scalar import TyScalar
   from jsonmlir.utils.enum_scalars import Scalar

   i64 = TyScalar(name=Scalar.i64)
   module = Module([
       Function(
           "add_one",
           [("value", i64)],
           [Binary("+", Var("value"), Const(1))],
       ),
   ])

Compile an input description with:

.. code-block:: console

   $ jsonmlir examples/somme/main.json -A

The ``-A`` option prints the AST, generated MLIR, optimized MLIR, and LLVM
stages. Use ``--link`` when the input has a matching ``.call.cpp`` wrapper and
you want an executable.

Input formats
-------------

The command accepts ``.json``, ``.yaml``, and ``.yml`` operation descriptions.
Python DSL programs can also be passed through the command's Python entry
point as shown in the repository examples.
