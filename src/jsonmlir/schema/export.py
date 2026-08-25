"""Export JSON Schema for the jsonMLIR AST (used by ts-ast generation)."""

from __future__ import annotations

from typing import Any

from pydantic import TypeAdapter
from pydantic.json_schema import JsonSchemaMode

from jsonmlir.schema.clean_for_ts import clean_ast_schema_for_ts


def export_ast_schema(*, mode: JsonSchemaMode = "serialization", for_ts: bool = False) -> dict[str, Any]:
    """Return the JSON Schema for the module AST root type."""
    from jsonmlir.operations.op_module import ModuleJsonOp

    schema = TypeAdapter(ModuleJsonOp).json_schema(mode=mode)
    if for_ts:
        schema = clean_ast_schema_for_ts(schema)
    return schema
