"""Isolated insertion point for type inspection without modifying the generated module."""

from __future__ import annotations

from mlir.ir import InsertionPoint, Module

# Disposable modules are kept alive because ValNodes may still reference
# operations inserted into them.
_discard_modules: list[Module] = []


def discard_builder() -> InsertionPoint:
    """Create a disposable block whose operations are not added to generation."""
    module = Module.create()
    _discard_modules.append(module)
    return InsertionPoint(module.body)
