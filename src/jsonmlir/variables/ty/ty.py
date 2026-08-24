from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Any, Union

from mlir.ir import MemRefType, Type
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from jsonmlir.utils.discriminants import normalize_ty_discriminant

"""ABC commune aux types valeur (scalaires, struct, array).

Les types sont des modèles Pydantic formant une union discriminée sur le champ
``type``. Un champ annoté ``TyNode`` accepte donc n'importe quelle description
JSON canonique :

- scalaire : ``{"type": "scalar", "name": "i64"}`` (ou le raccourci ``"i64"``)
- struct   : ``{"type": "struct", "name": "structName"}``
- memref   : ``{"type": "memref", "dims": [dim...], "base": type}``
- soa      : ``{"type": "soa",    "dims": [dim...], "base": "structName"}``
- buffer   : ``{"type": "buffer", "dims": [dim...], "base": "structName"}``
- ptr      : ``{"type": "ptr",    "base": type}``

Les formes historiques (``{"memref": [...]}``, ``{"addr": ...}``, ...) restent
acceptées en entrée via :func:`parse_ty`, qui les normalise en émettant un
``DeprecationWarning``.
"""


if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


class TyNode(BaseModel, ABC):
    # ``frozen`` : les types sont des valeurs, hachables et partageables.
    # ``populate_by_name`` : les champs restent accessibles sous leur nom Python
    # même lorsqu'ils portent un alias JSON (``dimensions`` / ``dims``).
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
        # Pydantic n'accepte que des arguments nommés : on mappe les arguments
        # positionnels sur les champs déclarés (hors discriminant "type").
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

    # ──────────── Type ────────────
    @abstractmethod
    def get_type(self) -> Type:
        raise NotImplementedError

    @abstractmethod
    def get_memref_type(self) -> MemRefType:
        raise NotImplementedError

    # ──────────── Pydantic ────────────
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        from pydantic_core import core_schema

        # Les sous-classes concrètes gardent le schéma de modèle standard ;
        # seule l'ABC se comporte comme l'union discriminée de tous les types.
        if not cls.__abstractmethods__:
            return handler(source_type)

        # Indirection par lambda : ``parse_ty`` / ``dump_ty`` sont définis plus
        # bas dans le module, après la classe qu'ils manipulent.
        return core_schema.no_info_plain_validator_function(
            lambda value: parse_ty(value),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda value: dump_ty(value), when_used="json"
            ),
        )


def dump_ty(value: TyNode) -> Any:
    """Sérialise un ``TyNode`` dans sa forme JSON canonique."""
    return value.model_dump(mode="json", by_alias=True)


_ty_adapter: TypeAdapter[Any] | None = None


def _adapter() -> TypeAdapter[Any]:
    """Union discriminée de tous les types, construite paresseusement.

    L'import différé casse le cycle ``ty`` -> ``ty_struct`` -> ``memory`` -> ``ty``.
    """
    global _ty_adapter
    if _ty_adapter is None:
        from jsonmlir.variables.ty.ty_buffer import TyBuffer
        from jsonmlir.variables.ty.ty_memref import TyMemref
        from jsonmlir.variables.ty.ty_ptr import TyPtr
        from jsonmlir.variables.ty.ty_scalar import TyScalar
        from jsonmlir.variables.ty.ty_SOA import TySOA
        from jsonmlir.variables.ty.ty_SSA import TySSA
        from jsonmlir.variables.ty.ty_struct import TyStruct

        _ty_adapter = TypeAdapter(
            Annotated[
                Union[  # noqa: UP007 - `Union[...]` requis dans un Annotated dynamique
                    TyScalar, TyStruct, TyMemref, TyBuffer, TySOA, TyPtr, TySSA
                ],
                Field(discriminator="type"),
            ]
        )
    return _ty_adapter


def _legacy(value: dict[str, Any]) -> dict[str, Any] | None:
    """Convertit une description de type historique en forme canonique."""
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


def parse_ty(value: Any) -> TyNode:
    """Construit le ``TyNode`` correspondant à une description JSON."""
    if isinstance(value, TyNode):
        return value

    # Raccourci scalaire : "i64" équivaut à {"type": "scalar", "name": "i64"}.
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

    return _adapter().validate_python(value)
