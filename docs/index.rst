jsonMLIR documentation
======================

jsonMLIR compiles JSON, YAML, or Python descriptions of functions into MLIR,
then lowers them through LLVM to native object files and executables.

The project provides both a JSON schema and a typed Python DSL. Use the DSL
when writing descriptions by hand, or generate the JSON representation from
another language and feed it to the ``jsonmlir`` command.

.. toctree::
   :maxdepth: 2
   :caption: Guides

   quickstart
   api

.. seealso::

   The `project README <https://github.com/LouisMaxHa/jsonMLIR>`_ contains the
   installation guide, command-line options, examples, and test instructions.
