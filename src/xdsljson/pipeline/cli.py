#!/usr/bin/env python3
"""Entry point for the xDSL-JSON compiler."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

_FLAG_ALIASES: dict[str, str] = {
    "T": "--tree",
    "P": "--mlir_passes",
    "m": "--mlir",
    "M": "--mlir_opti",
    "n": "--mlir_llvm",
    "l": "--llvm",
    "L": "--llvm_opti",
    "C": "--cmd",
    "A": "--all",
    "d": "--show-diff",
}

def _expand_grouped_trace_flags(argv: Sequence[str]) -> list[str]:
    expanded: list[str] = list(argv)
    for arg in argv:
        if not arg.startswith("-"):
            continue

        if not all(
            letter in _FLAG_ALIASES.keys()
            for letter in arg[1::]
        ):
            continue

        expanded.remove(arg)
        for letter in arg[1::]:
            expanded.append(_FLAG_ALIASES[letter])

    return expanded


def resolve_output_name(input_path: Path, explicit: str | None = None) -> str:
    """Nom de base des artefacts intermédiaires dans ``build/``.

    Pour ``main.json`` / ``main.py`` (exemples parallèles), utilise le nom du
    dossier parent afin d'éviter les conflits entre compilations concurrentes.
    """
    if explicit is not None:
        return explicit
    resolved = input_path.resolve()
    if resolved.stem == "main":
        return resolved.parent.name
    return resolved.stem


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="xdsljson",
        description=(
            "Compile a JSON/YAML description to MLIR, then to a native executable "
            "via the MLIR/LLVM toolchain."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input file (.json, .yaml, .yml, or .py).",
    )
    parser.add_argument(
        "-o",
        "--output-name",
        dest="output_name",
        default=None,
        metavar="NAME",
        help=(
            "Base name for intermediate build artifacts in build/ "
            "(default: parent folder for main.json/main.py, else input stem)."
        ),
    )
    parser.add_argument(
        "--mlir-bin-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing mlir-opt, mlir-translate, llc, and clang++ "
            "(otherwise MLIR_BIN_DIR or PATH)."
        ),
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root (for examples/ and build/).",
    )
    parser.add_argument(
        "-T",
        "--tree",
        action="store_true",
        help="Print the Python AST as a tree (codegen trace).",
    )
    parser.add_argument(
        "-P",
        "--mlir_passes",
        action="store_true",
        help="Print the IR after each MLIR pass.",
    )
    parser.add_argument(
        "-m",
        "--mlir",
        action="store_true",
        help="Print MLIR before optimization.",
    )
    parser.add_argument(
        "-M",
        "--mlir_opti",
        action="store_true",
        help="Print MLIR after optimization.",
    )
    parser.add_argument(
        "-n",
        "--mlir_llvm",
        action="store_true",
        help="Print the MLIR LLVM dialect.",
    )
    parser.add_argument(
        "-l",
        "--llvm",
        action="store_true",
        help="Print LLVM IR.",
    )
    parser.add_argument(
        "-L",
        "--llvm_opti",
        action="store_true",
        help="Print LLVM after optimization.",
    )
    parser.add_argument(
        "-C",
        "--cmd",
        action="store_true",
        help="Print mlir-opt, mlir-translate, llc, clang++, and other commands.",
    )
    parser.add_argument(
        "-A",
        "--all",
        action="store_true",
        help="Shortcut for tree+cmd+mlir+mlir_opti+llvm+llvm_opti.",
    )
    parser.add_argument(
        "-d",
        "--show-diff",
        action="store_true",
        help="Print a colored diff between each IR stage.",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help=(
            "Link the object file with main.call.cpp to produce an executable (.out)."
        ),
    )
    if argv is None:
        argv = sys.argv[1:]
    argv = _expand_grouped_trace_flags(argv)

    if "--all" in argv:
        for expend in [
            "--tree", "--cmd",
            "--mlir", "--mlir_opti",
            "--llvm", "--llvm_opti"
        ]:
            if expend not in argv:
                argv.append(expend)

    return parser.parse_args(argv)

if __name__ == "__main__":
    from xdsljson.pipeline.compiler import main

    raise SystemExit(main())
