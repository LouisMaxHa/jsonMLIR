"""Tests for JSON Schema export and ts-ast generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import TypeAdapter

if TYPE_CHECKING:
    from jsonmlir.operations.op_module import ModuleJsonOp

ROOT = Path(__file__).resolve().parents[1]
TS_AST = ROOT / "ts-ast"
GENERATOR = ROOT / "scripts" / "generate_ts_ast.py"
SOMME_JSON = ROOT / "examples" / "somme" / "main.json"


@pytest.fixture(scope="module")
def module_json_op_type() -> type[ModuleJsonOp]:
    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import tests.conftest  # pyright: ignore[reportUnusedImport]  # noqa: F401

    from jsonmlir.operations.op_module import ModuleJsonOp

    return ModuleJsonOp


def test_schema_export(module_json_op_type: type[ModuleJsonOp]) -> None:
    from jsonmlir.schema.export import export_ast_schema

    schema = export_ast_schema(mode="serialization")
    assert "$defs" in schema
    assert len(schema["$defs"]) >= 20


def test_schema_clean_for_ts():
    from jsonmlir.schema.export import export_ast_schema

    raw = export_ast_schema(mode="serialization", for_ts=False)
    cleaned = export_ast_schema(mode="serialization", for_ts=True)

    call_op = cleaned["$defs"]["CallOp"]
    assert call_op["additionalProperties"] is False
    assert "op" in call_op["required"]
    assert call_op["properties"]["op"]["const"] == "call"
    assert "default" not in call_op["properties"]["op"]
    assert cleaned.get("additionalProperties") is False

    assert "TyNode" in cleaned["$defs"]
    assert "TyNodeBase" not in cleaned["$defs"]
    assert "JsonOp" in cleaned["$defs"]
    assert cleaned["$defs"]["FunctionOp"]["properties"]["body"]["items"] == {
        "$ref": "#/$defs/JsonOp"
    }

    struct_field = cleaned["$defs"]["StructField"]
    assert struct_field["minItems"] == 4
    assert struct_field["items"][0]["type"] == "string"
    assert struct_field["items"][1]["$ref"] == "#/$defs/TyNode"

    # Le nettoyage ne modifie pas le schéma brut utilisé côté Python
    assert "TyNodeBase" in raw["$defs"]


def test_legacy_json_dual_read(module_json_op_type: type[ModuleJsonOp]) -> None:
    data = json.loads(SOMME_JSON.read_text(encoding="utf-8"))
    adapter: TypeAdapter[ModuleJsonOp] = TypeAdapter(module_json_op_type)
    module = adapter.validate_python(data)
    assert module.op == "module"


def test_json_round_trip(module_json_op_type: type[ModuleJsonOp]) -> None:
    adapter: TypeAdapter[ModuleJsonOp] = TypeAdapter(module_json_op_type)
    data = json.loads(SOMME_JSON.read_text(encoding="utf-8"))
    module = adapter.validate_python(data)
    dumped = module.model_dump(mode="json", by_alias=True)
    assert dumped["op"] == "module"
    assert dumped["body"][0]["op"] == "function"
    restored = adapter.validate_python(dumped)
    assert restored.model_dump(mode="json", by_alias=True) == dumped


def test_generator_produces_ts_ready_schema(tmp_path: Path) -> None:
    assert GENERATOR.is_file()
    out = tmp_path / "ast.schema.json"
    subprocess.run(
        [sys.executable, str(GENERATOR), str(out)],
        cwd=ROOT,
        check=True,
    )
    schema = json.loads(out.read_text(encoding="utf-8"))
    assert "$defs" in schema

    struct_field = schema["$defs"]["StructField"]
    assert struct_field["items"][1]["$ref"] == "#/$defs/TyNode"

    for op in ("DefineFunctionOp", "FunctionOp"):
        args = schema["$defs"][op]["properties"]["args"]["items"]
        assert args["items"][1]["$ref"] == "#/$defs/TyNode"


def test_typescript_example_validates_in_python(module_json_op_type: type[ModuleJsonOp]) -> None:
    if not TS_AST.is_dir():
        pytest.skip("ts-ast submodule not checked out")
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
    adapter: TypeAdapter[ModuleJsonOp] = TypeAdapter(module_json_op_type)
    module = adapter.validate_python(ts_json)
    assert module.op == "module"
    assert ts_json["body"][0]["name"] == "lib_main"
