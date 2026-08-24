"""Shared pytest fixtures (mlir stubs for schema-only tests)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from collections.abc import Sequence
from typing import Any


def _install_mlir_stubs() -> None:
    class _AutoStubModule(types.ModuleType):
        def __getattr__(self, name: str) -> Any:
            full = f"{self.__name__}.{name}"
            if full not in sys.modules:
                child = _AutoStubModule(full)
                if self.__name__ == "mlir" or name == "dialects":
                    child.__path__ = []  # type: ignore[attr-defined]
                sys.modules[full] = child
                setattr(self, name, child)
                return child
            return sys.modules[full]

    class _MlirLoader(importlib.util.Loader):
        def __init__(self, name: str) -> None:
            self.name = name

        def create_module(
            self, spec: importlib.machinery.ModuleSpec,
        ) -> types.ModuleType:
            mod = _AutoStubModule(spec.name)
            if spec.name == "mlir" or spec.name.endswith(".dialects"):
                mod.__path__ = []  # type: ignore[attr-defined]
            return mod

        def exec_module(self, module: types.ModuleType) -> None:
            sys.modules[module.__name__] = module

    class _MlirFinder:
        def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: types.ModuleType | None = None,
        ) -> importlib.machinery.ModuleSpec | None:
            if fullname == "mlir" or fullname.startswith("mlir."):
                return importlib.util.spec_from_loader(
                    fullname, _MlirLoader(fullname),
                )
            return None

    if not any(type(f).__name__ == "_MlirFinder" for f in sys.meta_path):
        sys.meta_path.insert(0, _MlirFinder())


_install_mlir_stubs()
