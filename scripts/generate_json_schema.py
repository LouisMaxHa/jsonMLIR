#!/usr/bin/env python3
"""Export Pydantic AST schema and generate TypeScript via json-schema-to-typescript.

Writes:
  - ts-ast/schema/ast.schema.json
  - ts-ast/generated/schema.ts  (via ``npm run generate`` in ts-ast)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def get_schema() -> dict[Any, Any]:
    from jsonmlir.schema.export import export_ast_schema
    return export_ast_schema(mode="serialization", for_ts=True)


def write_schema(path: Path, schema: dict[Any, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate json schema from Pydantic")
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output json schema file"
    )
    args = parser.parse_args()

    schema = get_schema()
    write_schema(args.output, schema)
    print(f"Json schema written at {args.output}")

if __name__ == "__main__":
    main()
