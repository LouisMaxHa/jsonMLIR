"""Point d'insertion isolé pour l'inspection de types sans modifier le module généré."""

from __future__ import annotations

from mlir.ir import InsertionPoint, Module

# Les modules jetables sont gardés vivants : des ValNodes peuvent encore
# référencer des opérations qui y ont été insérées.
_discard_modules: list[Module] = []


def discard_builder() -> InsertionPoint:
    """Bloc jetable, les opérations ne sont pas rajoutées à la génération"""
    module = Module.create()
    _discard_modules.append(module)
    return InsertionPoint(module.body)
