"""Post-traitement du JSON Schema Pydantic pour une génération TypeScript plus propre."""

from __future__ import annotations

import copy
from typing import Any

# Titres génériques Pydantic : json2ts en fait des alias (`Name`, `Name1`, …) au lieu d'inliner.
_GENERIC_PROPERTY_TITLES = frozenset(
    {
        "$Type",
        "Name",
        "Size",
        "Val",
        "Args",
        "Body",
        "Cond",
        "Dims",
        "Fields",
        "Indices",
        "Lhs",
        "Rhs",
        "Type",
        "Value",
        "Thenblock",
        "Elseblock",
        "Scalar",
    }
)

_JSON_OP_REFS = frozenset(
    {
        "#/$defs/AllocOp",
        "#/$defs/AllocaOp",
        "#/$defs/BinaryOp",
        "#/$defs/CallOp",
        "#/$defs/CondOp",
        "#/$defs/ConstOp",
        "#/$defs/MathOp",
        "#/$defs/PrintOp",
        "#/$defs/SetOp",
        "#/$defs/UnaryOp",
        "#/$defs/VarOp",
        "#/$defs/WhileOp",
    }
)


def _ty_node_schema(defs: dict[str, Any]) -> dict[str, Any]:
    """Union discriminée TyNode, extraite du schéma existant."""
    for candidate in ("DefineFunctionOp", "FunctionOp", "VarOp"):
        props = defs.get(candidate, {}).get("properties", {})
        args = props.get("args") or props.get("return_types")
        if not isinstance(args, dict):
            continue
        items = args.get("items")
        if isinstance(items, dict) and ("oneOf" in items or "discriminator" in items):
            return copy.deepcopy(items)
        prefix = items.get("prefixItems") if isinstance(items, dict) else None
        if isinstance(prefix, list) and len(prefix) >= 2:
            return copy.deepcopy(prefix[1])
    raise ValueError("Impossible d'extraire le schéma TyNode depuis $defs")


def _strip_generic_titles(node: Any) -> None:
    """Supprime les titres qui forcent json2ts à créer des alias inutiles."""
    if isinstance(node, dict):
        title = node.get("title")
        if title in _GENERIC_PROPERTY_TITLES:
            node.pop("title", None)
        for value in node.values():
            _strip_generic_titles(value)
    elif isinstance(node, list):
        for item in node:
            _strip_generic_titles(item)


def _set_additional_properties_false(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" and "additionalProperties" not in node:
            node["additionalProperties"] = False
        for value in node.values():
            _set_additional_properties_false(value)
    elif isinstance(node, list):
        for item in node:
            _set_additional_properties_false(item)


def _normalize_dollar_type(node: Any) -> None:
    """Inline les littéraux $type et les rend obligatoires."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            props = node.get("properties")
            if isinstance(props, dict) and "$type" in props:
                dollar = props["$type"]
                if isinstance(dollar, dict) and "const" in dollar:
                    dollar.pop("title", None)
                    dollar.pop("default", None)
                    required = node.setdefault("required", [])
                    if "$type" not in required:
                        required.append("$type")
        for value in node.values():
            _normalize_dollar_type(value)
    elif isinstance(node, list):
        for item in node:
            _normalize_dollar_type(item)


def _replace_refs(node: Any, mapping: dict[str, str]) -> None:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref in mapping:
            node["$ref"] = mapping[ref]
        for value in node.values():
            _replace_refs(value, mapping)
    elif isinstance(node, list):
        for item in node:
            _replace_refs(item, mapping)


def _fix_struct_field(defs: dict[str, Any], ty_node: dict[str, Any]) -> None:
    defs["StructField"] = {
        "type": "array",
        "minItems": 4,
        "maxItems": 4,
        "prefixItems": [
            {"type": "string"},
            copy.deepcopy(ty_node),
            {"type": "integer"},
            {"type": "integer"},
        ],
    }


def _add_ty_node_def(defs: dict[str, Any], ty_node: dict[str, Any]) -> None:
    defs["TyNode"] = ty_node


def _json_op_schema(defs: dict[str, Any]) -> dict[str, Any]:
    """Union discriminée des opérations IR dans le corps d'une fonction."""
    lhs = defs["BinaryOp"]["properties"]["lhs"]
    schema = copy.deepcopy(lhs)
    schema["title"] = "JsonOp"
    return schema


def _is_json_op_union(node: dict[str, Any]) -> bool:
    one_of = node.get("oneOf")
    if not isinstance(one_of, list):
        return False
    refs = {
        item["$ref"]
        for item in one_of
        if isinstance(item, dict) and isinstance(item.get("$ref"), str)
    }
    return refs == _JSON_OP_REFS


def _collapse_json_op_unions(node: Any) -> None:
    """Remplace les unions d'ops dupliquées par ``$ref: #/$defs/JsonOp``."""
    if isinstance(node, dict):
        if _is_json_op_union(node):
            node.clear()
            node["$ref"] = "#/$defs/JsonOp"
            return
        for value in node.values():
            _collapse_json_op_unions(value)
    elif isinstance(node, list):
        for item in node:
            _collapse_json_op_unions(item)


def clean_ast_schema_for_ts(schema: dict[str, Any]) -> dict[str, Any]:
    """Retourne une copie du schéma optimisée pour json-schema-to-typescript."""
    out = copy.deepcopy(schema)
    defs = out.setdefault("$defs", {})

    ty_node = _ty_node_schema(defs)
    json_op = _json_op_schema(defs)
    _add_ty_node_def(defs, ty_node)
    _fix_struct_field(defs, ty_node)

    _replace_refs(
        out,
        {
            "#/$defs/TyNodeBase": "#/$defs/TyNode",
        },
    )
    if "TyNodeBase" in defs:
        del defs["TyNodeBase"]

    _collapse_json_op_unions(out)
    defs["JsonOp"] = json_op

    _strip_generic_titles(out)
    _normalize_dollar_type(out)
    _set_additional_properties_false(out)

    return out
