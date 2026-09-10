#!/usr/bin/env python3
"""PoC 1 — Génération de classes TypeScript directement depuis les modèles Pydantic.

Remplace le pipeline ``json_schema.json + json-schema-to-typescript`` :
  - plus besoin de ``clean_ast_schema_for_ts`` (export_typescript.py),
  - plus de dépendance npm ``json-schema-to-typescript``,
  - les classes portent les valeurs par défaut des modèles Pydantic
    (discriminants ``op``/``type``, ``Scalar.i64``, ``None``, ``()``…).

Usage:
    python -m jsonmlir.schema.export_ts_classes schema.ts
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, get_args, get_origin

from pydantic import BaseModel

# Import de base.py : enregistre les ops dans le namespace pydantic (model_rebuild)
from jsonmlir.operations.op_alloc import AllocOp
from jsonmlir.operations.op_alloca import AllocaOp
from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.operations.op_call import CallOp
from jsonmlir.operations.op_cond import IfOp
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_define_function import DefineFunctionOp
from jsonmlir.operations.op_define_struct import DefineStructOp
from jsonmlir.operations.op_function import FunctionOp
from jsonmlir.operations.op_math import MathOp, MathOperator
from jsonmlir.operations.op_module import ModuleJsonOp
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.operations.op_print import PrintOp
from jsonmlir.operations.op_set import SetOp
from jsonmlir.operations.op_unary import UnaryOp, UnaryOperator
from jsonmlir.operations.op_var import VarOp
from jsonmlir.operations.op_while import WhileOp
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty import TyNodeBase
from jsonmlir.variables.ty.ty_buffer import TyBuffer
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_SOA import TySOA
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct

# ── Registres ──────────────────────────────────────────────────────────────

ENUMS = {
    "TyNode": set([TyScalar, TyStruct, TyMemref, TyBuffer, TySOA, TyPtr, TySSA]),
    "JsonOp": set([
        BinaryOp, CallOp, ConstOp, IfOp, VarOp, WhileOp,
        PrintOp, SetOp, AllocOp, AllocaOp, MathOp, UnaryOp,
    ]),
    "ModuleStatement": set([DefineStructOp, DefineFunctionOp, FunctionOp])
}

# List of all class
MODELS: list[Any] = [ModuleJsonOp]
for models in ENUMS.values():
    MODELS.extend(list(models))
MODELS.sort(key = lambda e: e.__name__)

ENUM_TS_NAMES = {
    Scalar: "Scalar",
    OperatorOp: "OperatorOp",
    UnaryOperator: "UnaryOperator",
    MathOperator: "MathOperator",
}

PRIMITIVES = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    type(None): "null",
}

# Mots réservés TypeScript : autorisés comme propriété, interdits comme paramètre.
RESERVED = {"var"}
DISCRIMINATORS = ("type", "op")

# Champs dont la forme JSON diffère de l'annotation Python
# (StructRef sérialisé en nom de struct, cf. PlainSerializer de ty_struct).
FIELD_OVERRIDES = {
    (TyBuffer.__name__, "base"): "string",
    (TySOA.__name__, "base"): "string",
}

""" ===================================================
    == Utils for type
    =================================================== """

def unwrap(ann: Any) -> Any:
    while get_origin(ann) is Annotated:
        ann = get_args(ann)[0]
    return ann


def union_parts(members: list[Any]) -> list[str]:
    """replace list of models by unions type if possible"""
    models = [m for m in members if isinstance(m, type) and issubclass(m, BaseModel)]

    for enum_name, enum_models in ENUMS.items():
        if set(models) == enum_models:
            return [enum_name]

    return [ts_type(m) for m in members]


def array_of(t: str) -> str:
    """Add parenthesis arround union if necessary"""
    return f"({t})[]" if " | " in t else f"{t}[]"


def ts_type(ann: Any) -> str:
    """Annote Python -> type TypeScript."""
    ann = unwrap(ann)

    # Primitive
    if ann in PRIMITIVES:
        return PRIMITIVES[ann]

    # Classe de modèle (ordre important : Enum < TyNodeBase < BaseModel)
    if isinstance(ann, type):
        if issubclass(ann, Enum):
            return ENUM_TS_NAMES[ann]
        if issubclass(ann, TyNodeBase):
            return "TyNode"
        if issubclass(ann, BaseModel):
            return ann.__name__

    origin = get_origin(ann)

    if origin is Literal:
        return " | ".join(json.dumps(v) for v in get_args(ann))

    # ValNode[Any] (valeurs déjà générées) -> JsonOp
    if "ValNode" in str(ann):
        return "JsonOp"

    if origin in (list, Sequence, tuple):
        args = get_args(ann)
        if origin is tuple and args and args[-1] is not Ellipsis:
            return "[" + ", ".join(ts_type(a) for a in args) + "]"
        elem = ts_type(args[0]) if args else "unknown"
        return array_of(elem)

    # Union (typing.Union / X | Y)
    members = list(get_args(ann))
    if members:
        parts = union_parts(members)
        # Collapse T[] alongside T (lhs: BaseValue | Sequence[ValNode[Any]] -> JsonOp)
        collapsed = [p for p in parts if not any(f"{p}[]" == q for q in parts)]
        parts = collapsed or parts
        return " | ".join(dict.fromkeys(parts))

    return "unknown"


def ts_default(ann: Any, value: Any) -> str:
    """Valeur par défaut python -> expression TypeScript."""
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, Sequence):
        return "[]"
    if isinstance(value, Enum):
        return json.dumps(value.value)
    return str(value)

""" ===================================================
    == Generate
    =================================================== """


def collect() -> dict[str, Any]:
    """Construit le contexte de génération."""
    # Enum of string
    enums = {
        name: [m.value for m in cls]
        for cls, name in ENUM_TS_NAMES.items()
    }

    # Unions (enum of tohers types)
    unions = {
        categorie: " | ".join(m.__name__ for m in models)
        for categorie, models in ENUMS.items()
    }
    unions["ReturnTypes"] = "TyNode[]"


    # Tuples
    tuples = {
        "StructField": "[string, TyNode, number, number]",
        "FunctionArg": "[string, TyNode]",
    }

    # Classes
    classes: list[dict[str, Any]] = []
    for model in MODELS:
        fields: list[dict[str, Any]] = []
        for fname, field in model.model_fields.items():

            # Name of the field
            name = field.alias or fname

            # Type of the field
            ftype = FIELD_OVERRIDES.get(
                (model.__name__, name),
                ts_type(field.annotation)
            )

            # Default value of the field
            required = field.is_required()
            default = None
            if not required:
                # default factory are used by list, return default empty list
                if field.default_factory is not None:
                    default = "[]"
                else:
                    default = ts_default(field.annotation, field.default)

            # arg name for the constructor
            argName = name
            if name in DISCRIMINATORS and not required:
                argName = None
            elif name in RESERVED:
                argName = f"{name}_"

            fields.append({
                "name": name, "argName": argName, "type": ftype,
                "required": required, "default": default
            })


        classes.append({
            "name": model.__name__, "fields": fields
        })

    return {
        "enums": enums,
        "unions": unions,
        "tuples": tuples,
        "classes": classes,
    }


""" ===================================================
    == Cli
    =================================================== """

def gen_default(f: Any):
    if f['default'] is None:
        return ""
    return f" = {f['default']}"


def render() -> str:
    """Génère le fichier TypeScript."""
    ctx = collect()
    out: str = ""
    EOL = "\n"

    # Header + enums
    out += "// Generated from Pydantic AST models — DO NOT EDIT." + EOL
    out += EOL
    out += "// Types" + EOL
    for name, values in ctx["enums"].items():
        literal = " | ".join(json.dumps(v) for v in values)
        out += f"export type {name} = {literal};" + EOL

    # Unions
    out += EOL
    out += "// Types union" + EOL
    for name, body in ctx["unions"].items():
        out += f"export type {name} = {body};" + EOL

    # Tuples
    out += EOL
    out += "// Tuples" + EOL
    for name, body in ctx["tuples"].items():
        out += f"export type {name} = {body};" + EOL

    # Classes
    out += EOL
    out += "// Class" + EOL
    for c in ctx["classes"]:
        # Classe attributs
        out += f"export class {c['name']} {{" + EOL
        for field in c["fields"]:
            out += f"\t{field['name']}: {field['type']}{gen_default(field)};" + EOL

        # Classe constructor
        args = [p for p in c["fields"] if p["argName"] is not None]
        # Required params before optional ones (TypeScript rule)
        required = [p for p in args if p["required"]]
        optional = [p for p in args if not p["required"]]
        args = required + optional
        out += EOL
        out += "\tconstructor(" + EOL
        for field in args:
            out += f"\t\t{field['argName']}: {field['type']}{gen_default(field)}," + EOL
        out += "\t) {" + EOL
        for field in args:
            out += f"\t\tthis.{field['name']} = {field['argName']};" + EOL
        out += "\t}" + EOL
        out += "}" + EOL

    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate TypeScript classes from Pydantic AST models"
    )
    parser.add_argument("output", type=Path, help="Path to the .ts file")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(), encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
