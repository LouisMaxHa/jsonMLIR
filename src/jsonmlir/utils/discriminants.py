"""Champs discriminants JSON partagés (``$type``) pour ops et types."""

from __future__ import annotations

from typing import Any

from pydantic import Field

_OP_TAGS = frozenset({
    "module", "function", "define_function", "define struct",
    "binary", "unary", "math", "const", "var", "set", "call",
    "while", "if", "print", "alloc", "alloca",
})

_TY_TAGS = frozenset({
    "scalar", "struct", "memref", "buffer", "soa", "ptr", "ssa",
})


def json_op_discriminator(value: str) -> str:
    """Discriminant d'opération : lit ``$type`` via validateur, émet ``$type``."""
    return Field(  # type: ignore[return-value]
        default=value,
        serialization_alias="$type",
    )


def json_ty_discriminator(value: str) -> str:
    """Discriminant de type : lit ``$type`` via validateur, émet ``$type``."""
    return Field(  # type: ignore[return-value]
        default=value,
        serialization_alias="$type",
    )


def normalize_dollar_type(data: Any) -> Any:
    """Réécrit récursivement ``$type`` en ``op`` ou ``type`` pour Pydantic."""
    if isinstance(data, list):
        return [normalize_dollar_type(item) for item in data]

    if not isinstance(data, dict):
        return data

    out: dict[str, Any] = {}
    for key, value in data.items():
        if key == "$type":
            continue
        out[key] = normalize_dollar_type(value)

    if "$type" in data:
        tag = data["$type"]
        if tag in _TY_TAGS and "type" not in out and "op" not in out:
            out["type"] = tag
        elif "op" not in out:
            out["op"] = tag

    return out


def normalize_op_discriminant(data: object) -> object:
    """Normalise un nœud op (niveau unique) avant validation Pydantic."""
    if isinstance(data, dict) and "$type" in data and "op" not in data:
        out = dict(data)
        out["op"] = out.pop("$type")
        return out
    return data


def normalize_ty_discriminant(data: object) -> object:
    """Normalise un nœud type (niveau unique) avant validation Pydantic."""
    if isinstance(data, dict) and "$type" in data and "type" not in data:
        out = dict(data)
        out["type"] = out.pop("$type")
        return out
    return data
