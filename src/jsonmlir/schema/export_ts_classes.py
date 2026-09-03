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
import types
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, Union, get_args, get_origin

import jinja2
from pydantic import BaseModel
from pydantic.fields import FieldInfo

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
MODELS = [
    ModuleJsonOp
] + [
    classModel
    for category in ENUMS.items()
    for classModel in category
]

ENUM_TS_NAMES = {
    Scalar: "Scalar",
    OperatorOp: "OperatorOp",
    UnaryOperator: "UnaryOperator",
    MathOperator: "MathOperator",
}

PRIMITIVES = {str: "string", int: "number", float: "number", bool: "boolean", type(None): "null"}

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


def is_union(ann: Any) -> bool:
    return get_origin(ann) in (Union, types.UnionType)

def ts_type(ann: Any) -> str:
    """Annote Python -> type TypeScript."""
    ann = unwrap(ann)

    if ann in PRIMITIVES:
        return PRIMITIVES[ann]

    if isinstance(ann, type) and issubclass(ann, Enum):
        return ENUM_TS_NAMES[ann]

    if isinstance(ann, type) and issubclass(ann, TyNodeBase):
        return "TyNode"

    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return ann.__name__

    origin = get_origin(ann)

    if origin is Literal:
        return " | ".join(json.dumps(v) for v in get_args(ann))

    # ValNode[Any] (valeurs déjà générées) -> JsonOp
    if "ValNode" in str(ann):
        return "JsonOp"

    if origin in (list, Sequence, tuple):
        args = get_args(ann)
        if not args:
            return "unknown[]"
        if origin is tuple and len(args) == 2 and args[1] is Ellipsis:
            return array_of(ts_type(args[0]))
        if origin is tuple:
            return "[" + ", ".join(ts_type(a) for a in args) + "]"
        return array_of(ts_type(args[0]))

    members = list(get_args(ann))
    if members == []:
        parts = union_parts(members)
        # Collapse T[] alongside T (lhs: BaseValue | Sequence[ValNodeAny] -> JsonOp)
        collapsed = [p for p in parts if not any(f"{p}[]" == q for q in parts)]
        parts = collapsed or parts
        return " | ".join(dict.fromkeys(parts))

    return "unknown"


def union_parts(members: list[Any]) -> list[str]:
    models = [m for m in members if isinstance(m, type) and issubclass(m, BaseModel)]
    excluded = [m for m in members if not isinstance(m, type) or not issubclass(m, BaseModel)]
    print(excluded)

    for setName, setModels in ENUMS:
        if set(models) == setModels:
            return [setName]

    return [ts_type(m) for m in members]


def array_of(t: str) -> str:
    return f"({t})[]" if " | " in t else f"{t}[]"

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

def filterNotNoneAttribut(elements: Any[], attr: str):
    return [ element
        for element in elements
        if element.get(attr, None) is not None
    ]

""" ===================================================
    == Generate
    =================================================== """


def collect() -> dict[str, Any]:
    """Construit le contexte du template jinja."""
    # Enum of string
    enums = {
        name: [m.value for m in cls]
        for cls, name in ENUM_TS_NAMES.items()
    }

    # Unions (enum of tohers types)
    unions = {
        categorie: " | ".join(m.__name__ for m in models)
        for categorie, models in ENUM
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
            ftype = FIELD_OVERRIDES.get((model.__name__, name)) or ts_type(
                field.annotation
            )

            # Default value
            default = None
            required = field.is_required()
            if not required:
                # default factory are used by list, return default empty list
                if field.default_factory is not None:
                    default = "[]"
                else:
                    default = ts_default(field.annotation, field.default)

            # arg name for the constructor
            argName = name
            if name in DISCRIMINATORS:
                argName = None
            if name in RESERVED:
                argName = f"{name}_" if name in RESERVED else name

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


def render() -> str:
    template = jinja2.Environment(
        loader=jinja2.PackageLoader("jsonmlir.schema", "templates"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    ).get_template("ts_classes.jinja2")
    return template.render(**collect(), filterNotNoneAttribut=filterNotNoneAttribut)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TypeScript classes from Pydantic AST models")
    parser.add_argument("output", type=Path, help="Path to the .ts file")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(), encoding="utf-8")
    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()