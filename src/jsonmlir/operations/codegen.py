from __future__ import annotations

from abc import ABC, ABCMeta, abstractmethod
from collections.abc import Sequence
from enum import EnumMeta
from typing import Any

from pydantic import BaseModel, ConfigDict

from jsonmlir.utils.schema_shape import ast_schema_extra
from jsonmlir.variables.val.val import ValNode


# ABC : Abstract Base Class
class OpNode(BaseModel, ABC):
    """ Abstract class that have a codegen() methode
    """

    # Required to allow non-Pydantic types in subclasses.
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_schema_extra=ast_schema_extra,
    )

    # Pydantic only accepts named arguments: map positional arguments to the
    # declared fields (excluding the "op" discriminator) for manual
    # instantiation, e.g. Const(1, "i32").
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            # Extract the method parameters.
            fields = [f for f in type(self).model_fields if f != "op"]

            # Check that a "name" argument is not already defined by a keyword.
            for name, value in zip(fields, args):
                if name in kwargs:
                    raise TypeError(
                        f"{type(self).__name__}: '{name}' already defined in kwargs"
                    )
                kwargs[name] = value
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return type(self).__name__

    # @abstractmethod forces subclasses to implement this abstract method.
    @abstractmethod
    def codegen(self) -> Sequence[ValNode[Any]]:
        """Generate the MLIR operation at the current insertion point and
        return a list of nodes containing the results."""
        raise NotImplementedError

class ABCEnumMeta(EnumMeta, ABCMeta):
    """Allow inheritance from both Enum and ValNode (ABC)."""
