from __future__ import annotations

from typing import Annotated, Any, Literal

from mlir.ir import MemRefType
from pydantic import BeforeValidator, PlainSerializer, PrivateAttr

from jsonmlir.utils.discriminants import json_ty_discriminator
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import STRUCTS_TYPE, structs_type
from jsonmlir.variables.ty.ty import TyNodeBase


class TyStruct(TyNodeBase):
    type: Literal["struct"] = json_ty_discriminator("struct")
    name: str

    # Résolution paresseuse : un struct peut être référencé avant sa définition.
    _resolved: STRUCTS_TYPE | None = PrivateAttr(default=None)

    def __init__(self, base: str | STRUCTS_TYPE | None = None, /, **kwargs: Any) -> None:
        resolved: STRUCTS_TYPE | None = None
        if base is not None:
            if isinstance(base, str):
                kwargs["name"] = base
            else:
                kwargs["name"] = base.NAME
                resolved = base
        super().__init__(**kwargs)
        self._resolved = resolved if resolved is not None else structs_type.get(self.name)

    @property
    def struct(self) -> STRUCTS_TYPE:
        if self._resolved is not None:
            return self._resolved
        if self.name not in structs_type:
            raise ValueError(f"Struct {self.name!r} is not defined")
        self._resolved = structs_type[self.name]
        return self._resolved

    def get_type(self) -> MemRefType:
        return MemRefType.get([self.struct.SIZE], Scalar.i8.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        return f"Struct({self.name!r})"


def _struct_from_name(value: Any) -> Any:
    return TyStruct(value) if isinstance(value, str) else value


# Un buffer / SOA porte toujours un struct : le JSON n'en garde que le nom.
StructRef = Annotated[
    TyStruct,
    BeforeValidator(_struct_from_name),
    PlainSerializer(lambda s: s.name, return_type=str, when_used="json"),
]
