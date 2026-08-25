#!/usr/bin/env python3
"""Export Pydantic AST schema and generate TypeScript via json-schema-to-typescript.

Writes:
  - ts-ast/schema/ast.schema.json
  - ts-ast/generated/schema.ts  (via ``npm run generate`` in ts-ast)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TS_AST = ROOT / "ts-ast"
SCHEMA_JSON = TS_AST / "schema" / "ast.schema.json"
SCHEMA_TS = TS_AST / "generated" / "schema.ts"


def _ensure_import_path() -> None:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))


def export_schema() -> dict:
    _ensure_import_path()
    # Stubs MLIR pour l'export hors Docker (voir tests/conftest.py)
    import tests.conftest  # noqa: F401

    from jsonmlir.schema.export import export_ast_schema

    return export_ast_schema(mode="serialization", for_ts=True)


def write_schema(path: Path) -> None:
    schema = export_schema()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def run_json2ts() -> None:
    subprocess.run(
        ["npm", "run", "generate"],
        cwd=TS_AST,
        check=True,
    )


def patch_schema_ts(path: Path) -> None:
    """Corrige les limites de json2ts sur les tuples typés (prefixItems + union)."""
    text = path.read_text(encoding="utf-8")
    replacements = {
        "export type StructField = [unknown, unknown, unknown, unknown];": (
            "export type StructField = [string, TyNode, number, number];"
        ),
        "args?: [unknown, unknown][];": "args?: [string, TyNode][];",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ts-ast from Pydantic JSON Schema")
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Only export ast.schema.json, skip json2ts",
    )
    args = parser.parse_args()

    write_schema(SCHEMA_JSON)
    if not args.schema_only:
        run_json2ts()
        patch_schema_ts(SCHEMA_TS)
        print(f"Generated {SCHEMA_TS}")


if __name__ == "__main__":
    main()
