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

from jsonmlir.schema.export import get_schema


def write(path: Path, txt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate JSON schema of the ast from Pydantic"
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the json schema.",
    )
    parser.add_argument(
        "--typescript",
        action="store_true",
        help="Improve compatibility of JSON schema for typescript",
    )

    args = parser.parse_args()

    schema = get_schema(for_typescript=args.typescript)
    schema_txt = json.dumps(schema, indent=2) + "\n"
    write(args.output, schema_txt)
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
