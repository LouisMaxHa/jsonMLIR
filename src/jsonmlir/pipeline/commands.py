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
from pydantic import TypeAdapter

from jsonmlir.operations.op_module import ModuleJsonOp


# Path -> Json
def load_input_file(path: Path) -> Any:
    """Load a JSON or YAML file and return the corresponding dictionary.

    Example:

    .. code-block:: python

       data_json = load_input_file(Path("program.json"))
       data_yaml = load_input_file(Path("program.yaml"))
    """

    if not path.is_file():
        raise ValueError(f"Error: file not found: {path}")


    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    try:
        if suffix == ".json":
            return json.loads(text)
        if suffix in (".yaml", ".yml"):
            return yaml.safe_load(text)

        raise ValueError(
            f"Unsupported file extension: {suffix!r}. "
            "Use .json, .yaml, or .yml."
        )

    except (ValueError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Error loading {path}: {exc}", file=sys.stderr)
        raise ValueError(f"Error loading {path}: {exc}")


# Json -> Pydantic
def build_ast(data: Any) -> ModuleJsonOp:
    """Validate input data and build the corresponding module.


    .. code-block:: python

       data_json = load_input_file(Path("program.json"))
       ast = build_ast(data_json)
    """
    adapter: TypeAdapter[ModuleJsonOp] = TypeAdapter(ModuleJsonOp)
    return adapter.validate_python(data)

@dataclass(frozen=True)
class Toolchain:
    """Absolute paths to the required MLIR/LLVM binaries.

    You can instantiate Toolchain class manyally and specify each path manyally.
    Otherwise, you can use `Toolchain.discover()` to detect toolchain from venv or path.
    """

    mlir_opt: Path
    mlir_translate: Path
    llvm_opt: Path
    llc: Path
    clangxx: Path

    @classmethod
    def discover(
        cls,
        bin_dir: Path | None = None,
    ) -> Toolchain:
        """Locate the MLIR/LLVM tools.

        Priority order: ``bin_dir`` (CLI option), the ``MLIR_BIN_DIR``
        environment variable, the ``[tool.jsonmlir] mlir-bin-dir`` key in
        ``pyproject.toml``, then ``PATH``.
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
                    "- environment variable MLIR_BIN_DIR\n"
                    "- directory on PATH"
                )
                print(
                    f"Error: {name} not found.\n"
                    f"Specify the toolchain through:\n{hint}",
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

# Get the examples directory.
def _examples_include_dir(project_root: Path | None = None) -> Path:
    """Shared C++ header directory (memref_bridge.h)."""
    root = project_root or Path.cwd()
    return (root / "examples").resolve()

_display_cmd: bool = False
def set_display_cmd(state: bool) -> None:
    """Enable or disable printing of external compiler commands.

    Example:

    .. code-block:: python

       set_display_cmd(True)
    """
    global _display_cmd
    _display_cmd = state

def run_command(cmd: Sequence[str]) -> str:
    """Run a toolchain command and return its standard output.

    Args:
        cmd: Executable and arguments passed to :func:`subprocess.run`.

    Raises:
        ValueError: If the command exits unsuccessfully.

    Example:

    .. code-block:: python

       version = run_command(["mlir-opt", "--version"])
    """
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
        raise ValueError("Failed to run command")


# Apply MLIR passes
#   - MLIR -> MLIR Opti
#   - MLIR -> LLVM MLIR
def run_mlir_opt(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path,
    passes: list[str],
    display_passes: bool = False
) -> None:
    """Run ``mlir-opt`` with a sequence of transformation passes."""
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
) -> None:
    """Translate MLIR in the LLVM dialect into LLVM IR."""
    run_command([
        str(toolchain.mlir_translate),
        "--mlir-to-llvmir",
        str(input_path),
        "-o", str(output_path)
    ])

# LLVM -> relocatable object file (.o)
def run_llvm_opt(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path,
    passes: list[str]
) -> None:
    """Run LLVM optimization passes on an LLVM IR file."""
    run_command([
        str(toolchain.llvm_opt),
        f"-passes={','.join(passes)}",
        str(input_path),
        "-S", # Emit LLVm and not bytecode
        "-o", str(output_path),
    ])

# LLVM -> relocatable object file (.o)
def compile_llvm_to_object(
    toolchain: Toolchain,
    input_path: Path,
    output_path: Path
) -> None:
    """Compile LLVM IR into a relocatable object file."""
    run_command([
        str(toolchain.llc),
        "-O2",
        "-filetype=obj",
        "-relocation-model=pic",
        str(input_path),
        "-o", str(output_path),
    ])

# Object + call wrapper -> executable
def link_executable(
    toolchain: Toolchain,
    call_source: Path,
    object_path: Path,
    output_path: Path,
    *,
    project_root: Path | None = None
) -> None:
    """Link generated object code and a C++ call wrapper into an executable."""
    include_dir = _examples_include_dir(project_root)
    run_command([
        str(toolchain.clangxx),
        "-std=c++20",
        str(object_path),
        str(call_source),
        f"-I{include_dir}",
        "-o", str(output_path),
    ])
