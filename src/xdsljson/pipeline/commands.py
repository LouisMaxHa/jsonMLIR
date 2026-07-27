from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from mlir.ir import Module
from pydantic import TypeAdapter

from xdsljson.operations.op_module import ModuleJsonOp


# Path -> Json
def load_input_file(path: Path) -> Any:
    """Charge un fichier JSON ou YAML et renvoie le dictionnaire correspondant."""

    if not path.is_file():
        print(f"Erreur : fichier introuvable : {path}", file=sys.stderr)
        return 1


    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    try:
        if suffix == ".json":
            return json.loads(text)
        if suffix in (".yaml", ".yml"):
            return yaml.safe_load(text)

    except (ValueError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Erreur lors du chargement de {path} : {exc}", file=sys.stderr)
        raise

    raise ValueError(
        f"Extension de fichier non supportée : {suffix!r}. "
        "Utilisez .json, .yaml ou .yml."
    )

# Json -> Pydantic
def build_sample_ast_json(data: Any) -> ModuleJsonOp:
    adapter: TypeAdapter[ModuleJsonOp] = TypeAdapter(ModuleJsonOp)
    return adapter.validate_python(data)

@dataclass(frozen=True)
class Toolchain:
    """Chemins absolus vers les binaires MLIR/LLVM requis."""

    mlir_opt: Path
    mlir_translate: Path
    llvm_opt: Path
    llc: Path
    clangxx: Path

    @classmethod
    def discover(
        cls,
        bin_dir: Path | None = None,
        project_root: Path | None = None,
    ) -> Toolchain:
        """Localise les outils MLIR/LLVM.

        Ordre de priorité : ``bin_dir`` (option CLI), variable d'environnement
        ``MLIR_BIN_DIR``, clé ``[tool.xdsljson] mlir-bin-dir`` du
        ``pyproject.toml``, puis le ``PATH``.
        """
        search_dirs: list[Path] = []
        if bin_dir is not None:
            search_dirs.append(bin_dir.expanduser().resolve())
        env_dir = os.environ.get("MLIR_BIN_DIR")
        if env_dir:
            search_dirs.append(Path(env_dir).expanduser().resolve())

        names = ("mlir-opt", "mlir-translate", "opt", "llc", "clang++")
        resolved: dict[str, Path] = {}

        for name in names:
            path: Path | None = None
            for directory in search_dirs:
                candidate = directory / name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    path = candidate
                    break
            if path is None:
                found = shutil.which(name)
                if found is not None:
                    path = Path(found)
            if path is None:
                hint = (
                    "- option --mlir-bin-dir\n"
                    "- variable d'environnement MLIR_BIN_DIR\n"
                    "- répertoire sur PATH"
                )
                print(
                    f"Erreur : {name} introuvable.\n"
                    f"Indiquez la toolchain via :\n{hint}",
                    file=sys.stderr,
                )
                sys.exit(1)
            resolved[name] = path

        return cls(
            mlir_opt=resolved["mlir-opt"],
            mlir_translate=resolved["mlir-translate"],
            llvm_opt=resolved["opt"],
            llc=resolved["llc"],
            clangxx=resolved["clang++"],
        )

# Get examples directory ?
def examples_include_dir(project_root: Path | None = None) -> Path:
    """Répertoire d'en-têtes C++ partagés (memref_bridge.h)."""
    root = project_root or Path.cwd()
    return (root / "examples").resolve()

_display_cmd: bool = False
def set_display_cmd(state: bool):
    global _display_cmd
    _display_cmd = state

def run_command(cmd: Sequence[str]) -> str:
    name = Path(cmd[0]).name
    if _display_cmd:
        print(shlex.join(cmd).replace(" -", "\n\t-"))

    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        print()
        print(f"Error when running {name} :", file=sys.stderr)
        print("Full command:", " ".join(cmd).replace(" -", "\n\t-"))
        print()

        if exc.stdout:
            print("stdout:", exc.stdout)

        print('\033[91m' + exc.stderr + '\033[0m', file=sys.stderr)
        exit(1)


# Écrit le module MLIR en texte
def write_mlir(module: Module, output_path: Path):
    output_path.write_text(str(module), encoding="utf-8")


# Apply MLIR passes
#   - MLIR -> MLIR Opti
#   - MLIR -> LLVM MLIR
def run_mlir_opt(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path,
    passes: list[str],
    display_passes: bool = False
):
    if display_passes:
        passes.append("--mlir-print-ir-after-all")

    run_command([
        str(toolchain.mlir_opt),
        *passes,
        str(input_path),
        "-o", str(output_path),
    ])

# MLIR dialect LLVM -> LLVM
def convert_to_llvm(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path
):
    run_command([
        str(toolchain.mlir_translate),
        "--mlir-to-llvmir",
        str(input_path),
        "-o", str(output_path)
    ])

# LLVM -> fichier objet relocatable (.o)
def run_llvm_opt(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path,
    passes: list[str]
):
    run_command([
        str(toolchain.llvm_opt),
        f"-passes={','.join(passes)}",
        str(input_path),
        "-S", # Emit LLVm and not bytecode
        "-o", str(output_path),
    ])

# LLVM -> fichier objet relocatable (.o)
def compile_llvm_to_object(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path
) -> None:
    run_command([
        str(toolchain.llc),
        "-O2",
        "-filetype=obj",
        "-relocation-model=pic",
        str(input_path),
        "-o", str(output_path),
    ])

# Objet + call -> exécutable
def link_executable(
    toolchain: Toolchain,
    call_source: Path,
    object_path: Path,
    output_path: Path,
    *,
    project_root: Path | None = None
) -> None:
    include_dir = examples_include_dir(project_root)
    run_command([
        str(toolchain.clangxx),
        str(object_path),
        str(call_source),
        f"-I{include_dir}",
        "-o", str(output_path),
    ])
