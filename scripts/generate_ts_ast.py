#!/usr/bin/env python3
"""Generate TypeScript AST classes from jsonMLIR Pydantic models.

Writes only under ``ts-ast/generated/``. Run from the repository root::

    python scripts/generate_ts_ast.py
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import inspect
import json
import re
import shutil
import sys
import types
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any, ForwardRef, Union, get_args, get_origin
import types

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "ts-ast" / "generated"


def _install_mlir_stubs() -> None:
    """Stub the whole ``mlir`` package so models import without native bindings."""

    class _AutoStubModule(types.ModuleType):
        def __getattr__(self, name: str) -> Any:
            full = f"{self.__name__}.{name}"
            if full not in sys.modules:
                child = _AutoStubModule(full)
                if self.__name__ == "mlir" or name == "dialects":
                    child.__path__ = []  # type: ignore[attr-defined]
                sys.modules[full] = child
                setattr(self, name, child)
                return child
            return sys.modules[full]

    class _MlirLoader(importlib.util.Loader):
        def __init__(self, name: str) -> None:
            self.name = name

        def create_module(
            self, spec: importlib.machinery.ModuleSpec,
        ) -> types.ModuleType:
            mod = _AutoStubModule(spec.name)
            if spec.name == "mlir" or spec.name.endswith(".dialects"):
                mod.__path__ = []  # type: ignore[attr-defined]
            return mod

        def exec_module(self, module: types.ModuleType) -> None:
            sys.modules[module.__name__] = module

    class _MlirFinder:
        def find_spec(
            self,
            fullname: str,
            path: Sequence[str] | None,
            target: types.ModuleType | None = None,
        ) -> importlib.machinery.ModuleSpec | None:
            if fullname == "mlir" or fullname.startswith("mlir."):
                return importlib.util.spec_from_loader(
                    fullname, _MlirLoader(fullname),
                )
            return None

    if not any(type(f).__name__ == "_MlirFinder" for f in sys.meta_path):
        sys.meta_path.insert(0, _MlirFinder())


def _ensure_import_path() -> None:
    _install_mlir_stubs()
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    _stub_packages_without_init()


def _stub_packages_without_init() -> None:
    """Register packages without executing heavy ``__init__.py`` modules."""
    pkg_roots = [
        ("jsonmlir", SRC / "jsonmlir"),
        ("jsonmlir.operations", SRC / "jsonmlir" / "operations"),
        ("jsonmlir.variables", SRC / "jsonmlir" / "variables"),
        ("jsonmlir.variables.ty", SRC / "jsonmlir" / "variables" / "ty"),
        ("jsonmlir.variables.val", SRC / "jsonmlir" / "variables" / "val"),
        ("jsonmlir.utils", SRC / "jsonmlir" / "utils"),
    ]
    for name, path in pkg_roots:
        if name in sys.modules:
            continue
        pkg = types.ModuleType(name)
        pkg.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = pkg


def _version() -> str:
    try:
        import subprocess

        out = subprocess.check_output(
            ["git", "describe", "--tags", "--always"],
            cwd=ROOT,
            text=True,
        ).strip()
        return out
    except Exception:
        return "dev"


@dataclass
class FieldSpec:
    py_name: str
    json_name: str
    ts_type: str
    optional: bool = False
    default_empty: bool = False  # omit when [] or equivalent


@dataclass
class ModelSpec:
    name: str
    discriminant_value: str | None
    fields: list[FieldSpec]
    side_effect: str | None = None


@dataclass
class EnumSpec:
    name: str
    members: list[tuple[str, str]]  # (ts_name, json_value)


# ── Type mapping ──────────────────────────────────────────────────────────

_OP_CLASS_NAMES = [
    "BinaryOp", "CallOp", "ConstOp", "CondOp", "DefineFunctionOp",
    "DefineStructOp", "FunctionOp", "ModuleJsonOp", "PrintOp", "SetOp",
    "UnaryOp", "WhileOp", "AllocOp", "AllocaOp", "MathOp", "VarOp",
]

_TY_CLASS_NAMES = [
    "TyScalar", "TyStruct", "TyMemref", "TyBuffer", "TySOA", "TyPtr", "TySSA",
]

_BASE_VALUE = [
    "BinaryOp", "CallOp", "ConstOp", "CondOp", "VarOp", "WhileOp",
    "PrintOp", "SetOp", "AllocOp", "AllocaOp", "MathOp", "UnaryOp",
]

_MODULE_STATEMENT = ["DefineStructOp", "DefineFunctionOp", "FunctionOp"]

_SET_VALUE = ["BinaryOp", "ConstOp", "VarOp", "CallOp", "UnaryOp"]

_TYPE_ALIASES: dict[str, str] = {
    "OperatorOp": "Operator",
    "UnaryOperator": "UnaryOperator",
    "MathOperator": "MathOperator",
    "BaseValue": "BaseValue",
    "ModuleStatement": "ModuleStatement",
    "TyNode": "TyNode",
    "VarOp": "VarOp",
    "Scalar": "Scalar",
    "FIELD_TYPE": "FieldType",
}


def _preload_core_modules() -> None:
    """Load schema-related modules without triggering operations/__init__.py."""
    preload = [
        "jsonmlir/utils/discriminants.py",
        "jsonmlir/utils/enum_scalars.py",
        "jsonmlir/utils/trace.py",
        "jsonmlir/variables/memory.py",
        "jsonmlir/variables/ty/ty.py",
        "jsonmlir/variables/ty/ty_scalar.py",
        "jsonmlir/variables/ty/ty_struct.py",
        "jsonmlir/variables/ty/ty_memref.py",
        "jsonmlir/variables/ty/ty_buffer.py",
        "jsonmlir/variables/ty/ty_SOA.py",
        "jsonmlir/variables/ty/ty_ptr.py",
        "jsonmlir/variables/ty/ty_SSA.py",
        "jsonmlir/variables/val/val.py",
        "jsonmlir/operations/codegen.py",
        "jsonmlir/operations/op_operator.py",
        "jsonmlir/operations/base.py",
    ]
    for rel in preload:
        path = SRC / rel
        mod_name = "jsonmlir." + rel.replace("/", ".")[:-3]
        if mod_name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)


def _resolve_class(name: str) -> type[Any]:
    if name.startswith("Ty"):
        rel = f"variables/ty/{_camel_to_snake(name)}.py"
    else:
        rel = f"operations/{_camel_to_snake(name)}.py"
    path = SRC / "jsonmlir" / rel
    mod_name = f"jsonmlir.{rel.replace('/', '.').removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, name)


_OP_MODULE_OVERRIDES: dict[str, str] = {
    "ConstOp": "op_constant",
    "ModuleJsonOp": "op_module",
    "CondOp": "op_cond",
}


def _camel_to_snake(name: str) -> str:
    if name in _OP_MODULE_OVERRIDES:
        return _OP_MODULE_OVERRIDES[name]
    if name.startswith("Ty"):
        rest = name[2:]
        if rest == "SOA":
            return "ty_SOA"
        if rest == "SSA":
            return "ty_SSA"
        return "ty_" + rest[0].lower() + rest[1:]
    base = name.replace("Op", "")
    return "op_" + _snake(base)


def _snake(s: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", s).lower()


def _json_field_name(model: type[Any], py_name: str) -> str:
    info = model.model_fields[py_name]
    alias = info.serialization_alias or info.alias
    return alias if alias else py_name


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    origin = get_origin(annotation)
    if origin is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0], True
    return annotation, False


def _annotation_to_ts(annotation: Any, field_name: str = "") -> str:
    if isinstance(annotation, ForwardRef):
        return _annotation_to_ts(annotation.__forward_arg__, field_name)

    if isinstance(annotation, str):
        if annotation in _TYPE_ALIASES:
            return _TYPE_ALIASES[annotation]
        if annotation in _OP_CLASS_NAMES or annotation in _TY_CLASS_NAMES:
            return annotation
        if annotation in _BASE_VALUE:
            return "BaseValue"
        if annotation in _SET_VALUE:
            return "SetValue"
        return annotation

    annotation, _optional = _unwrap_optional(annotation)
    origin = get_origin(annotation)

    if origin is list or origin is Sequence:
        inner = get_args(annotation)[0]
        inner_origin = get_origin(inner)
        if inner_origin is tuple:
            targs = get_args(inner)
            if len(targs) == 2:
                return f"readonly [string, {_annotation_to_ts(targs[1], field_name)}][]"
        return f"readonly {_annotation_to_ts(inner, field_name)}[]"

    if origin is tuple:
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return f"readonly ({_annotation_to_ts(args[0], field_name)} | null)[]"
        if len(args) == 2:
            return f"readonly [string, {_annotation_to_ts(args[1], field_name)}]"
        inner = args[0] if args else "unknown"
        return f"readonly {_annotation_to_ts(inner, field_name)}[]"

    if isinstance(annotation, type):
        if issubclass(annotation, Enum):
            return _TYPE_ALIASES.get(annotation.__name__, annotation.__name__)
        if annotation.__name__ in _TYPE_ALIASES:
            return _TYPE_ALIASES[annotation.__name__]
        if annotation.__name__ in _OP_CLASS_NAMES or annotation.__name__ in _TY_CLASS_NAMES:
            return annotation.__name__

    if hasattr(annotation, "__name__"):
        name = annotation.__name__
        if name in _TYPE_ALIASES:
            return _TYPE_ALIASES[name]
        if name in _OP_CLASS_NAMES or name in _TY_CLASS_NAMES:
            return name

    if origin is Union:
        parts = []
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            part = _annotation_to_ts(arg, field_name)
            if part not in parts:
                parts.append(part)
        if parts == ["number"]:
            return "number"
        return " | ".join(parts)

    if annotation in (int, float):
        return "number"
    if annotation is str:
        return "string"
    if annotation is bool:
        return "boolean"

    args = get_args(annotation)
    if args and all(isinstance(a, str) for a in args):
        return "string"

    return "unknown"


def _discriminant_value(model: type[Any]) -> str | None:
    if "op" in model.model_fields:
        field = model.model_fields["op"]
        for meta in (field.default, field.default_factory):
            if isinstance(meta, str):
                return meta
        # Field() default
        default = field.default
        if default is not None and default is not ...:
            return str(default)
    if "type" in model.model_fields and model.__name__.startswith("Ty"):
        field = model.model_fields["type"]
        default = field.default
        if isinstance(default, str):
            return default
    return None


def _model_from_pydantic(cls: type[Any]) -> ModelSpec:
    fields: list[FieldSpec] = []
    skip = {"op", "type"} if cls.__name__.startswith("Ty") else {"op"}

    for py_name, info in cls.model_fields.items():
        if py_name in skip:
            continue
        json_name = _json_field_name(cls, py_name)
        ann = info.annotation
        _, is_optional = _unwrap_optional(ann)

        # SetOp uses `var` in JSON
        ts_name = "var_" if py_name == "var" and cls.__name__ == "SetOp" else py_name
        if py_name == "var" and cls.__name__ == "SetOp":
            json_name = "var"

        ts_type = _annotation_to_ts(ann, py_name)
        if py_name == "val" and cls.__name__ == "SetOp":
            ts_type = "SetValue"

        default_empty = False
        ann_origin = get_origin(ann)
        if ann_origin in (list, Sequence, tuple):
            if py_name in ("indices", "body", "thenBlock", "return_types", "args", "size"):
                default_empty = True
        if py_name == "elseBlock":
            is_optional = True

        fields.append(
            FieldSpec(
                py_name=ts_name,
                json_name=json_name,
                ts_type=ts_type,
                optional=is_optional,
                default_empty=default_empty,
            )
        )

    return ModelSpec(
        name=cls.__name__,
        discriminant_value=_discriminant_value(cls),
        fields=fields,
        side_effect=None,
    )


def _collect_models() -> list[ModelSpec]:
    models: list[ModelSpec] = []
    for name in _OP_CLASS_NAMES + _TY_CLASS_NAMES:
        cls = _resolve_class(name)
        models.append(_model_from_pydantic(cls))
    return models


def _collect_enums() -> list[EnumSpec]:
    from jsonmlir.operations.op_math import MathOperator
    from jsonmlir.operations.op_operator import OperatorOp
    from jsonmlir.operations.op_unary import UnaryOperator
    from jsonmlir.utils.enum_scalars import Scalar

    specs: list[EnumSpec] = []

    def from_enum(name: str, enum_cls: type[Enum]) -> EnumSpec:
        members = [(m.name, m.value) for m in enum_cls]  # type: ignore[attr-defined]
        return EnumSpec(name=name, members=members)

    specs.append(from_enum("Scalar", Scalar))
    specs.append(from_enum("Operator", OperatorOp))
    specs.append(from_enum("UnaryOperator", UnaryOperator))
    specs.append(from_enum("MathOperator", MathOperator))
    return specs


# ── Code generation ───────────────────────────────────────────────────────

_HEADER = """\
// DO NOT EDIT — generated by scripts/generate_ts_ast.py
// jsonMLIR AST schema version: {version}
"""


def _emit_enum(spec: EnumSpec) -> str:
    lines = [f"export enum {spec.name} {{"]
    for ts_name, value in spec.members:
        safe = ts_name
        if safe in ("+", "-", "*", "/", "!", "==", "!=", "<", ">", "<=", ">="):
            safe = f"_{safe.replace('=', 'eq').replace('!', 'not').replace('<', 'lt').replace('>', 'gt')}"
        # Use quoted keys for special chars
        if re.match(r"^[a-zA-Z_]\w*$", ts_name):
            lines.append(f"    {ts_name} = {json.dumps(value)},")
        else:
            lines.append(f"    {json.dumps(ts_name)} = {json.dumps(value)},")
    lines.append("}")
    return "\n".join(lines)


def _emit_field_type_class() -> str:
    return '''
export class FieldType {
    constructor(
        readonly name: string,
        readonly type: TyNode,
        readonly offset: number,
        readonly size: number,
    ) {}

    toJSON(): unknown {
        return [this.name, toJsonValue(this.type), this.offset, this.size];
    }
}
'''.strip()


def _emit_to_json_helper() -> str:
    return '''
export function toJsonValue(value: unknown): unknown {
    if (value === undefined || value === null) {
        return undefined;
    }
    if (typeof value === 'object' && value !== null && 'toJSON' in value
        && typeof (value as { toJSON: unknown }).toJSON === 'function') {
        return (value as { toJSON: () => unknown }).toJSON();
    }
    if (Array.isArray(value)) {
        return value.map(v => toJsonValue(v));
    }
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        return value;
    }
    return value;
}
'''.strip()


def _emit_model(spec: ModelSpec) -> str:
    disc = spec.discriminant_value
    ctor_params = []
    props = []
    for f in spec.fields:
        opt = "?" if f.optional else ""
        props.append(f"        readonly {f.py_name}{opt}: {f.ts_type},")
        ctor_params.append(f"        readonly {f.py_name}{opt}: {f.ts_type},")

    body_lines = ["        const out: Record<string, unknown> = {", f"            $type: {json.dumps(disc)},"]
    for f in spec.fields:
        key = f.json_name
        if f.optional:
            body_lines.append(
                f"            ...({f'this.{f.py_name} !== undefined' if f.py_name != 'elseBlock' else f'this.{f.py_name} !== undefined && this.{f.py_name} !== null'} ? {{ {json.dumps(key)}: toJsonValue(this.{f.py_name}) }} : {{}}),"
            )
        elif f.default_empty:
            body_lines.append(
                f"            ...((this.{f.py_name}?.length ?? 0) > 0 ? {{ {json.dumps(key)}: toJsonValue(this.{f.py_name}) }} : {{}}),"
            )
        else:
            body_lines.append(f"            {json.dumps(key)}: toJsonValue(this.{f.py_name}),")

    body_lines.append("        };")
    body_lines.append("        return out;")

    side = ""
    if spec.side_effect:
        side = f"\n        {spec.side_effect};"

    return f"""
export class {spec.name} {{
    readonly $type = {json.dumps(disc)} as const;

    constructor(
{chr(10).join(ctor_params) if ctor_params else "        // no fields"}
    ) {{{side}
    }}

    toJSON(): Record<string, unknown> {{
{chr(10).join(body_lines)}
    }}
}}
""".strip()


def _emit_ty_scalar_special() -> str:
    """TyScalar serializes as a bare string when used standalone."""
    return '''
export class TyScalar extends TyNodeBase {
    readonly $type = 'scalar' as const;

    constructor(readonly name: Scalar) {
        super();
    }

    override toJSON(): unknown {
        return this.name;
    }
}
'''.strip()


def _emit_unions() -> str:
    return f"""
export type BaseValue =
    {' | '.join(_BASE_VALUE)};

export type ModuleStatement =
    {' | '.join(_MODULE_STATEMENT)};

export type SetValue =
    {' | '.join(_SET_VALUE)};

export type TyNode =
    {' | '.join(_TY_CLASS_NAMES)};
""".strip()


def _emit_ty_node_base() -> str:
    return '''
export abstract class TyNodeBase {
    abstract readonly $type: string;
    abstract toJSON(): unknown;
}
'''.strip()


def generate(output_dir: Path) -> None:
    _ensure_import_path()

    models = _collect_models()
    enums = _collect_enums()
    version = _version()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # index.ts
    index_parts = [_HEADER.format(version=version), _emit_to_json_helper(), _emit_ty_node_base()]

    for enum in enums:
        index_parts.append(_emit_enum(enum))

    index_parts.append(_emit_field_type_class())
    index_parts.append(_emit_unions())

    for spec in models:
        if spec.name == "TyScalar":
            index_parts.append(_emit_ty_scalar_special())
        elif spec.name.startswith("Ty"):
            # TyNode subclasses extend TyNodeBase
            disc = spec.discriminant_value
            fields = spec.fields
            ctor = "\n".join(
                f"        readonly {f.py_name}{'?' if f.optional else ''}: {f.ts_type},"
                for f in fields
            )
            body = ["        const out: Record<string, unknown> = {", f"            $type: {json.dumps(disc)},"]
            for f in fields:
                body.append(f"            {json.dumps(f.json_name)}: toJsonValue(this.{f.py_name}),")
            body.append("        };")
            body.append("        return out;")
            index_parts.append(f"""
export class {spec.name} extends TyNodeBase {{
    readonly $type = {json.dumps(disc)} as const;

    constructor(
{ctor}
    ) {{
        super();
    }}

    override toJSON(): Record<string, unknown> {{
{chr(10).join(body)}
    }}
}}
""".strip())
        else:
            index_parts.append(_emit_model(spec))

    index_parts.append(f"\nexport const JSONMLIR_AST_VERSION = {json.dumps(version)};\n")

    (output_dir / "index.ts").write_text("\n\n".join(index_parts) + "\n", encoding="utf-8")
    print(f"Generated {output_dir / 'index.ts'} ({len(models)} models, {len(enums)} enums)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ts-ast from Pydantic models")
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Output directory (default: ts-ast/generated)",
    )
    args = parser.parse_args()
    generate(args.output.resolve())


if __name__ == "__main__":
    main()
