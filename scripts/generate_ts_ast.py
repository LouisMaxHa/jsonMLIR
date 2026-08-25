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


def get_schema() -> str:
    from jsonmlir.schema.export import export_ast_schema

    schema = export_ast_schema(mode="serialization", for_ts=True)
    txt = json.dumps(schema, indent=2) + "\n"

    replacements = {
        "export type StructField = [unknown, unknown, unknown, unknown];": (
            "export type StructField = [string, TyNode, number, number];"
        ),
        "args?: [unknown, unknown][];": "args?: [string, TyNode][];",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt


def write(path: Path, txt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate JSON schema of the ast from Pydantic")
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the json schema.",
    )
    args = parser.parse_args()

    schema = get_schema()
    write(args.output, schema)
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
    main()
