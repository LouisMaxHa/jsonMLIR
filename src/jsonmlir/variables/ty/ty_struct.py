from __future__ import annotations

from typing import Annotated, Any, Literal

from mlir.ir import MemRefType
from pydantic import BeforeValidator, PlainSerializer, PrivateAttr

from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import StructDescriptor, structs_registry
from jsonmlir.variables.ty.ty import TyNodeBase


class TyStruct(TyNodeBase):
    """Represent a named externally-defined struct.

    The layout is resolved from the struct registry when the type is lowered.
    Struture are lazy evaluated, you can reference them by name and define them after.

    Arguments are:
    - if `base` is `StructDescriptor`: Pass anonymous structures
    - if `base` is `String`: Check struct registry for definition
    - if `base` is `None`: If name is passed thru Pydantic kwargs
    - `kargs["name"]`: Name of the struct, equivalent to base is String.

    Example:

    .. code-block:: python

       TyStruct("Point")
    """
    type: Literal["struct"] = "struct"
    name: str

    # Lazy resolution: a struct may be referenced before it is defined.
    _resolved: StructDescriptor | None = PrivateAttr(default=None)

    def __init__(self, base: str | StructDescriptor | None = None, /, **kwargs: Any) -> None:
        # Set name
        if isinstance(base, str):
            kwargs["name"] = base
        if isinstance(base, StructDescriptor):
            kwargs["name"] = base.name
        super().__init__(**kwargs)

        # Resolve
        if isinstance(base, StructDescriptor):
            self._resolved = base
        else:
            self._resolved = structs_registry.get(self.name, None)

    @property
    def struct(self) -> StructDescriptor:
        # Try to resolve
        if self._resolved is None:
            self._resolved = structs_registry.get(self.name, None)

        # Return
        if self._resolved is not None:
            return self._resolved

        # Or fail
        raise ValueError(f"Struct {self.name!r} is not defined")

    def get_type(self) -> MemRefType:
        return MemRefType.get([self.struct.size], Scalar.i8.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Struct({self.name!r})"

# TODO: Why?
def _struct_from_name(value: Any) -> Any:
    return TyStruct(value) if isinstance(value, str) else value


# A buffer / SOA always contains a struct; JSON stores only its name.
StructRef = Annotated[
    TyStruct,
    BeforeValidator(_struct_from_name),
    PlainSerializer(lambda s: s.name, return_type=str, when_used="json"),
]
