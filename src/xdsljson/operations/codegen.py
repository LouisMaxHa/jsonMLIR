from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Sequence
from enum import EnumMeta
from typing import Any

from pydantic import BaseModel, ConfigDict
from xdsl.builder import Builder

from xdsljson.variables.val.val import ValNode


# ABC : Abstract Base Class
class OpNode(BaseModel, ABC):
    # Necessaire pour autoriser les classes externes (xDSL: Builder)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Pydantic n'accepte que des arguments nommés : on mappe les arguments
        # positionnels sur les champs déclarés (hors discriminant "op") pour
        # permettre l'instanciation manuelle, ex. Const(1, "i32").
        if args:
            fields = [f for f in type(self).model_fields if f != "op"]
            if len(args) > len(fields):
                raise TypeError(
                    f"{type(self).__name__} accepte au plus {len(fields)} "
                    f"arguments positionnels, {len(args)} reçus"
                )
            for name, value in zip(fields, args):
                if name in kwargs:
                    raise TypeError(
                        f"{type(self).__name__}: '{name}' fourni à la fois en "
                        "positionnel et en mot-clé"
                    )
                kwargs[name] = value
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return type(self).__name__

    # Force les sous-classes à implémenter cette méthode abstraite
    @abstractmethod
    def codegen(self, builder: Builder) -> Sequence[ValNode]:
        """Génère l'opération xDSL et retourne la SSA produite."""
        raise NotImplementedError

class ABCEnumMeta(EnumMeta, ABCMeta):
    """Permet d'hériter à la fois de Enum et de ValNode (ABC)."""
