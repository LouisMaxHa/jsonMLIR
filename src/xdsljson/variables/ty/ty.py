from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from mlir.ir import MemRefType, Type

"""ABC commune aux types valeur (scalaires, struct, array).

``TyNode`` expose un schéma Pydantic (``__get_pydantic_core_schema__``) afin que
les types puissent être décrits directement en JSON et validés automatiquement
partout où un champ est annoté ``TyNode``. Les formes acceptées sont :

- scalaire : ``"i64"`` / ``"index"`` / ...
- struct   : ``{"struct": "structName"}`` (référence un struct défini)
- memref   : ``{"memref": [dim..., base]}`` (la base est elle-même un type)
- soa      : ``{"soa"   : [dim..., base]}``
- buffer   : ``{"buffer": [dim..., base]}``
- addr     : ``{"addr"  : base}``
"""


if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


class TyNode(ABC):
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

        return core_schema.no_info_plain_validator_function(
            parse_ty,
            serialization=core_schema.plain_serializer_function_ser_schema(
                repr, when_used="json"
            ),
        )


def parse_ty(value: Any) -> TyNode:
    """Construit le ``TyNode`` correspondant à une description JSON."""
    # Imports différés pour éviter les imports circulaires.
    from xdsljson.utils.enum_scalars import Scalar
    from xdsljson.variables.ty.ty_buffer import TyBuffer
    from xdsljson.variables.ty.ty_memref import TyMemref
    from xdsljson.variables.ty.ty_ptr import TyPtr
    from xdsljson.variables.ty.ty_scalar import TyScalar
    from xdsljson.variables.ty.ty_SOA import TySOA
    from xdsljson.variables.ty.ty_struct import TyStruct

    if isinstance(value, TyNode):
        return value

    if isinstance(value, str):
        return TyScalar(Scalar(value))

    if isinstance(value, dict):
        if "addr" in value.keys():
            return TyPtr(
                base=parse_ty(value["addr"])
            )

        if "memref" in value.keys():
            *dimensions, base = value["memref"]
            return TyMemref(dimensions=tuple(dimensions), base=parse_ty(base))

        if "soa" in value.keys():
            *dimensions, base = value["soa"]
            return TySOA(base=TyStruct(base), n_elements=tuple(dimensions))

        if "buffer" in value.keys():
            *dimensions, base = value["buffer"]
            return TyBuffer(dimensions=tuple(dimensions), base=TyStruct(base))

        if "struct" in value.keys():
            return TyStruct(value["struct"])

        if "name" in value.keys():
            return TyStruct(value["name"])

    raise ValueError(f"Description de type non reconnue : {value!r}")
