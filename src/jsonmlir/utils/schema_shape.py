"""Configure the JSON schema of AST models for clean TypeScript generation.

Applied through ``ConfigDict(json_schema_extra=...)`` on the ``OpNode`` and
``TyNodeBase`` bases, the Pydantic schema exposes strict objects
(``additionalProperties: false``) and required ``op`` / ``type`` discriminators
without defaults, without changing Python validation behavior.
"""

from __future__ import annotations

from typing import Any, cast

# Discriminator fields for unions: ``op`` for operations and ``type`` for types.
# See ``Field(discriminator=...)`` in ``op_module.py`` / ``ty.py``.
_DISCRIMINANT_FIELDS = ("op", "type")


def ast_schema_extra(schema: dict[str, Any], _model_class: type) -> None:
    """Return an object schema with ``additionalProperties: false`` and
    required discriminators without ``default`` (avoiding useless json2ts aliases)."""
    if schema.get("type") != "object":
        return

    properties = schema.get("properties")
    props = cast(dict[str, Any], properties) if isinstance(properties, dict) else {}
    for key in _DISCRIMINANT_FIELDS:
        disc = props.get(key)
        if isinstance(disc, dict) and "const" in disc:
            discriminant = cast(dict[str, Any], disc)
            discriminant.pop("title", None)
            discriminant.pop("default", None)
            required = schema.setdefault("required", [])
            if key not in required:
                required.append(key)

    schema.setdefault("additionalProperties", False)
