"""Tests for the shared JSON AST schema ($type discriminants, TS generation)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]
TS_AST = ROOT / "ts-ast"
GENERATED = TS_AST / "generated" / "index.ts"
GENERATOR = ROOT / "scripts" / "generate_ts_ast.py"
SOMME_JSON = ROOT / "examples" / "somme" / "main.json"


def _import_jsonmlir():
    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from jsonmlir.operations.op_module import ModuleJsonOp

    return ModuleJsonOp


@pytest.fixture(scope="module")
def module_json_op_type():
    return _import_jsonmlir()


def test_legacy_json_dual_read(module_json_op_type):
    """Historical JSON with ``op`` still validates."""
    data = json.loads(SOMME_JSON.read_text(encoding="utf-8"))
    adapter: TypeAdapter = TypeAdapter(module_json_op_type)
    module = adapter.validate_python(data)
    assert module.op == "module"


def test_dollar_type_round_trip(module_json_op_type):
    """``model_dump(by_alias=True)`` emits ``$type`` and round-trips."""
    adapter: TypeAdapter = TypeAdapter(module_json_op_type)
    data = json.loads(SOMME_JSON.read_text(encoding="utf-8"))
    module = adapter.validate_python(data)
    dumped = module.model_dump(mode="json", by_alias=True)
    assert dumped["$type"] == "module"
    assert dumped["body"][0]["$type"] == "function"
    assert "op" not in dumped
    restored = adapter.validate_python(dumped)
    assert restored.model_dump(mode="json", by_alias=True) == dumped


def test_generator_is_up_to_date():
    """``ts-ast/generated`` matches ``scripts/generate_ts_ast.py`` output."""
    assert GENERATOR.is_file()
    before = GENERATED.read_text(encoding="utf-8") if GENERATED.is_file() else ""
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
    )
    after = GENERATED.read_text(encoding="utf-8")
    assert before == after, "Regenerate with: python scripts/generate_ts_ast.py"


def test_typescript_example_validates_in_python(module_json_op_type):
    """JSON emitted by the TypeScript DSL decodes in Python."""
    if not (TS_AST / "node_modules").is_dir():
        pytest.skip("Run npm install in ts-ast first")
    proc = subprocess.run(
        ["npm", "run", "example"],
        cwd=TS_AST,
        capture_output=True,
        text=True,
        check=True,
    )
    ts_json = json.loads(proc.stdout)
    adapter: TypeAdapter = TypeAdapter(module_json_op_type)
    module = adapter.validate_python(ts_json)
    assert module.op == "module"
    assert ts_json["body"][0]["name"] == "lib_main"
