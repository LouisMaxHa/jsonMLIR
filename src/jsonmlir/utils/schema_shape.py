"""Configuration du schéma JSON des modèles AST pour une génération TS propre.

Appliqué via ``ConfigDict(json_schema_extra=...)`` sur les bases ``OpNode`` et
``TyNodeBase`` : le schéma généré par Pydantic expose alors des objets stricts
(``additionalProperties: false``) et des discriminants ``op`` / ``type``
obligatoires sans défaut — sans changer le comportement de validation Python.
"""

from __future__ import annotations

from typing import Any, cast

# Champs discriminants des unions : ``op`` pour les opérations, ``type`` pour
# les types. Voir ``Field(discriminator=...)`` dans ``op_module.py`` / ``ty.py``.
_DISCRIMINANT_FIELDS = ("op", "type")


def ast_schema_extra(schema: dict[str, Any], _model_class: type) -> None:
    """Retourne un schéma objet avec ``additionalProperties: false`` et les
    discriminants requis sans ``default`` (évite les alias json2ts inutiles)."""
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
