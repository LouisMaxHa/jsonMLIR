#!/usr/bin/env python3
"""Génère une librairie partagée `libmax.so` contenant une fonction
`max(int a, int b)` en utilisant les bindings Python de MLIR.

Étapes :
  1. Construction du module MLIR (dialectes `func` et `arith`).
  2. Abaissement (lowering) vers le dialecte LLVM via un PassManager.
  3. Émission d'un fichier objet avec l'ExecutionEngine.
  4. Édition de liens en librairie partagée avec le compilateur C du système.
  5. Test de la librairie via ctypes.

Prérequis : PYTHONPATH doit pointer vers
`build/tools/mlir/python_packages/mlir_core` (voir instructions.md).
"""
# Les bindings MLIR sont du Python non typé (pas de stubs) : le mode strict
# ne peut pas s'appliquer. On garde l'analyse Pyright en mode basic.
# pyright: basic

import ctypes
import os
import subprocess
import tempfile

from mlir.dialects import arith, func
from mlir.execution_engine import ExecutionEngine
from mlir.ir import Context, InsertionPoint, IntegerType, Location, Module, UnitAttr
from mlir.passmanager import PassManager


def build_module() -> Module:
    """Construit le module MLIR contenant la fonction max."""
    module = Module.create()
    i64 = IntegerType.get_signless(64)
    with InsertionPoint(module.body):

        @func.FuncOp.from_py_func(i64, i64, name="max")
        def _max(a, b):
            return arith.maxsi(a, b)

        # L'interface C (_mlir_ciface_max) facilite l'appel depuis d'autres
        # langages, même si le symbole `max` brut suffit ici avec ctypes.
        _max.func_op.attributes["llvm.emit_c_interface"] = UnitAttr.get()

    return module


def lower_to_llvm(module: Module) -> Module:
    """Abaisse le module vers le dialecte LLVM."""
    pm = PassManager.parse(
        "builtin.module(convert-func-to-llvm,convert-arith-to-llvm,"
        "reconcile-unrealized-casts)"
    )
    pm.run(module.operation)
    return module


def emit_shared_library(module: Module, output: str) -> None:
    """Émet un fichier objet puis le lie en librairie partagée."""
    engine = ExecutionEngine(module, opt_level=3)
    with tempfile.TemporaryDirectory() as tmp:
        obj = os.path.join(tmp, "max.o")
        engine.dump_to_object_file(obj)
        subprocess.run(["cc", "-shared", "-o", output, obj], check=True)


def main() -> None:
    with Context(), Location.unknown():
        module = build_module()
        print("=== Module MLIR ===")
        print(module)

        lower_to_llvm(module)
        emit_shared_library(module, "libmax.so")

    print("Librairie générée : libmax.so")

    # Vérification avec ctypes.
    lib = ctypes.CDLL(os.path.abspath("libmax.so"))
    lib.max.argtypes = [ctypes.c_int64, ctypes.c_int64]
    lib.max.restype = ctypes.c_int64
    for a, b in [(3, 7), (42, -5), (-10, -20)]:
        print(f"max({a}, {b}) = {lib.max(a, b)}")


if __name__ == "__main__":
    main()
