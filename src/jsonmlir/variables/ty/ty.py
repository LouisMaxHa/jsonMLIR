from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Any, cast

from mlir.ir import MemRefType, Type
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, TypeAdapter

from jsonmlir.utils.schema_shape import ast_schema_extra

"""ABC commune aux types valeur (scalaires, struct, array).

Les types concrets forment une union discriminée ``TyNode`` sur le champ
``type``. Les formes historiques restent acceptées via :func:`parse_ty`
à la frontière JSON.
"""

class TyNodeBase(BaseModel, ABC):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra=ast_schema_extra,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if args:
            names = [f for f in type(self).model_fields if f != "type"]
            if len(args) > len(names):
                raise TypeError(
                    f"{type(self).__name__} accepte au plus {len(names)} "
                    f"arguments positionnels, {len(args)} reçus"
                )
            for name, value in zip(names, args):
                if name in kwargs:
                    raise TypeError(
                        f"{type(self).__name__}: '{name}' fourni à la fois en "
                        "positionnel et en mot-clé"
                    )
                kwargs[name] = value
        super().__init__(**kwargs)

    @abstractmethod
    def get_type(self) -> Type:
        raise NotImplementedError

    @abstractmethod
    def get_memref_type(self) -> MemRefType:
        raise NotImplementedError

# LMX Vraiment nécéssaire ?
def dump_ty(value: TyNodeBase) -> Any:
    """Sérialise un type dans sa forme JSON canonique."""
    return value.model_dump(mode="json", by_alias=True)
# LMX fin

def _coerce_ty_node(value: Any) -> Any:
    """Accepte raccourcis (``\"i64\"``) et formes legacy en entrée de champ ``TyNode``."""
    if isinstance(value, TyNodeBase):
        return value
    if isinstance(value, (str, dict)):
        return parse_ty(value)
    return value


# Champs imbriqués (``TyPtr.base``, ``TyMemref.base``) : même coercition JSON que
# ``TyNode``, sans importer l'union (elle contient déjà TyPtr / TyMemref).

TyNested = Annotated[TyNodeBase, BeforeValidator(_coerce_ty_node)]


# Les types concrets sont importés APRÈS la définition de ``TyNodeBase`` /
# ``TyNested`` : ils en héritent, et les importer plus tôt déclencherait un
# import circulaire (``ty`` <-> ``ty_*``).
from jsonmlir.variables.ty.ty_buffer import TyBuffer
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_SOA import TySOA
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct


union = Annotated[
    TyScalar | TyStruct | TyMemref | TyBuffer | TySOA | TyPtr | TySSA,
    Field(discriminator="type"),
]

# LMX Est-ce vraiment nécéssaire ?
_ty_adapter_instance: TypeAdapter[Any] | None = None
def _get_ty_union_adapter() -> TypeAdapter[Any]:
    global _ty_adapter_instance
    if _ty_adapter_instance is None:
        _ty_adapter_instance = TypeAdapter(union)
    return _ty_adapter_instance

# LMX FIN


if TYPE_CHECKING:
    TyNode = union
    TyNested = TyNode
else:
    TyNode = Annotated[union, BeforeValidator(_coerce_ty_node)]


def parse_ty(value: Any) -> TyNodeBase:
    """Construit le type correspondant à une description JSON (y compris legacy)."""
    if isinstance(value, TyNodeBase):
        return value

    def convert_to_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            return {"type": "scalar", "name": value}

        elif isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            if "type" in value_dict:
                return value_dict

            if "addr" in value_dict:
                return {"type": "ptr", "base": value_dict["addr"]}

            for kind in ("memref", "soa", "buffer"):
                if kind in value_dict:
                    raw = cast(list[Any], value_dict[kind])
                    dimensions, base = raw[:-1], raw[-1]
                    return {"type": kind, "dims": dimensions, "base": base}

            for key in ("struct", "name"):
                if key in value_dict:
                    return {"type": "struct", "name": value_dict[key]}

        return {"legacy": value}

    return _get_ty_union_adapter().validate_python(convert_to_dict(value))
