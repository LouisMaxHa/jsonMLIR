from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Any, Union

from mlir.ir import MemRefType, Type
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, BeforeValidator, model_validator

from jsonmlir.utils.discriminants import normalize_ty_discriminant

"""ABC commune aux types valeur (scalaires, struct, array).

Les types concrets forment une union discriminée ``TyNode`` sur le champ
``type`` (alias JSON ``$type``). Les formes historiques restent acceptées
via :func:`parse_ty` à la frontière JSON.
"""


class TyNodeBase(BaseModel, ABC):
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_discriminant(cls, data: Any) -> Any:
        return normalize_ty_discriminant(data)

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


def dump_ty(value: TyNodeBase) -> Any:
    """Sérialise un type dans sa forme JSON canonique."""
    return value.model_dump(mode="json", by_alias=True)


_ty_adapter_instance: TypeAdapter[Any] | None = None


def _get_ty_union_adapter() -> TypeAdapter[Any]:
    global _ty_adapter_instance
    if _ty_adapter_instance is None:
        from jsonmlir.variables.ty.ty_buffer import TyBuffer
        from jsonmlir.variables.ty.ty_memref import TyMemref
        from jsonmlir.variables.ty.ty_ptr import TyPtr
        from jsonmlir.variables.ty.ty_scalar import TyScalar
        from jsonmlir.variables.ty.ty_SOA import TySOA
        from jsonmlir.variables.ty.ty_SSA import TySSA
        from jsonmlir.variables.ty.ty_struct import TyStruct

        _ty_adapter_instance = TypeAdapter(
            Annotated[
                Union[  # noqa: UP007
                    TyScalar,
                    TyStruct,
                    TyMemref,
                    TyBuffer,
                    TySOA,
                    TyPtr,
                    TySSA,
                ],
                Field(discriminator="type"),
            ]
        )
    return _ty_adapter_instance


def _coerce_ty_node(value: Any) -> Any:
    """Accepte raccourcis (``\"i64\"``) et formes legacy en entrée de champ ``TyNode``."""
    if isinstance(value, TyNodeBase):
        return value
    if isinstance(value, (str, dict)):
        return parse_ty(value)
    return value


def _build_ty_node_alias() -> Any:
    from jsonmlir.variables.ty.ty_buffer import TyBuffer
    from jsonmlir.variables.ty.ty_memref import TyMemref
    from jsonmlir.variables.ty.ty_ptr import TyPtr
    from jsonmlir.variables.ty.ty_scalar import TyScalar
    from jsonmlir.variables.ty.ty_SOA import TySOA
    from jsonmlir.variables.ty.ty_SSA import TySSA
    from jsonmlir.variables.ty.ty_struct import TyStruct

    union = Annotated[
        Union[  # noqa: UP007
            TyScalar,
            TyStruct,
            TyMemref,
            TyBuffer,
            TySOA,
            TyPtr,
            TySSA,
        ],
        Field(discriminator="type"),
    ]
    return Annotated[union, BeforeValidator(_coerce_ty_node)]


if TYPE_CHECKING:
    from jsonmlir.variables.ty.ty_buffer import TyBuffer
    from jsonmlir.variables.ty.ty_memref import TyMemref
    from jsonmlir.variables.ty.ty_ptr import TyPtr
    from jsonmlir.variables.ty.ty_scalar import TyScalar
    from jsonmlir.variables.ty.ty_SOA import TySOA
    from jsonmlir.variables.ty.ty_SSA import TySSA
    from jsonmlir.variables.ty.ty_struct import TyStruct

    TyNode = Annotated[
        Union[TyScalar, TyStruct, TyMemref, TyBuffer, TySOA, TyPtr, TySSA],
        Field(discriminator="type"),
    ]
else:
    TyNode = _build_ty_node_alias()


def _legacy(value: dict[str, Any]) -> dict[str, Any] | None:
    if "addr" in value:
        return {"type": "ptr", "base": value["addr"]}

    for kind in ("memref", "soa", "buffer"):
        if kind in value:
            *dimensions, base = value[kind]
            return {"type": kind, "dims": dimensions, "base": base}

    for key in ("struct", "name"):
        if key in value:
            return {"type": "struct", "name": value[key]}

    return None


def parse_ty(value: Any) -> TyNodeBase:
    """Construit le type correspondant à une description JSON (y compris legacy)."""
    if isinstance(value, TyNodeBase):
        return value

    if isinstance(value, str):
        value = {"type": "scalar", "name": value}

    elif isinstance(value, dict):
        if "$type" in value and "type" not in value:
            value = {**value, "type": value["$type"]}
        if "type" not in value:
            legacy = _legacy(value)
            if legacy is None:
                raise ValueError(f"Description de type non reconnue : {value!r}")
            warnings.warn(
                f"Forme de type obsolète {value!r} ; utiliser {legacy!r}.",
                DeprecationWarning,
                stacklevel=2,
            )
            value = legacy

    return _get_ty_union_adapter().validate_python(value)
