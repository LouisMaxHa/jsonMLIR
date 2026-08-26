"""Post-traitement du JSON Schema Pydantic pour une génération TypeScript plus propre."""

from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter
from pydantic.json_schema import JsonSchemaMode

from jsonmlir.schema.export_typescript import clean_ast_schema_for_ts


def get_schema(
    mode: JsonSchemaMode = "serialization", for_typescript: bool = False
) -> dict[str, Any]:
    """Return the JSON Schema for the module AST root type."""
    from jsonmlir.operations.op_module import ModuleJsonOp

    schema = TypeAdapter(ModuleJsonOp).json_schema(mode=mode)
    if for_typescript:
        schema = clean_ast_schema_for_ts(schema)
    return schema
