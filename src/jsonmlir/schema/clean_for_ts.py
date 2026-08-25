"""Post-traitement du JSON Schema Pydantic pour une génération TypeScript plus propre."""

from __future__ import annotations

import copy
from typing import Any, cast

# Titres génériques Pydantic
_GENERIC_PROPERTY_TITLES = frozenset(
    {
        "Name",
        "Op",
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
        props = cast(dict[str, Any], defs.get(candidate, {}).get("properties", {}))
        args = cast(dict[str, Any], props.get("args") or props.get("return_types"))
        items = args.get("items")
        if isinstance(items, dict):
            items_dict = cast(dict[str, Any], items)
            if "oneOf" in items_dict or "discriminator" in items_dict:
                return copy.deepcopy(items_dict)
            prefix = items_dict.get("prefixItems")
            if isinstance(prefix, list):
                prefix_items = cast(list[Any], prefix)
                if len(prefix_items) >= 2:
                    return copy.deepcopy(cast(dict[str, Any], prefix_items[1]))
    raise ValueError("Impossible d'extraire le schéma TyNode depuis $defs")


def _strip_generic_titles(node: Any) -> None:
    """Supprime les titres qui forcent json2ts à créer des alias inutiles."""
    if isinstance(node, dict):
        node_dict = cast(dict[str, Any], node)
        title = node_dict.get("title")
        if title in _GENERIC_PROPERTY_TITLES:
            node_dict.pop("title", None)
        for value in node_dict.values():
            _strip_generic_titles(value)
        return
    
    if isinstance(node, list):
        for item in cast(list[Any], node):
            _strip_generic_titles(item)


def _replace_refs(node: Any, mapping: dict[str, str]) -> None:
    if isinstance(node, dict):
        node_dict = cast(dict[str, Any], node)
        ref = node_dict.get("$ref")
        if isinstance(ref, str) and ref in mapping:
            node_dict["$ref"] = mapping[ref]
        for value in node_dict.values():
            _replace_refs(value, mapping)
        return

    if isinstance(node, list):
        for item in cast(list[Any], node):
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
    refs: set[str] = set()
    for item in cast(list[Any], one_of):
        if not isinstance(item, dict):
            continue
        ref = cast(dict[str, Any], item).get("$ref")
        if isinstance(ref, str):
            refs.add(ref)
    return frozenset(refs) == _JSON_OP_REFS


def _collapse_json_op_unions(node: Any) -> None:
    """Remplace les unions d'ops dupliquées par ``$ref: #/$defs/JsonOp``."""
    if isinstance(node, dict):
        node_dict = cast(dict[str, Any], node)
        if _is_json_op_union(node_dict):
            node_dict.clear()
            node_dict["$ref"] = "#/$defs/JsonOp"
            return
        for value in node_dict.values():
            _collapse_json_op_unions(value)
    elif isinstance(node, list):
        for item in cast(list[Any], node):
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

    return out
