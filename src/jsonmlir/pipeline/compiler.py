"""Orchestration de la compilation JSON/YAML → exécutable natif."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from mlir.ir import Context, InsertionPoint, Location, Module

from jsonmlir.operations.op_module import ModuleJsonOp
from jsonmlir.pipeline.cli import parse_args, resolve_output_name
from jsonmlir.pipeline.commands import (
    Toolchain,
    build_sample_ast_json,
    compile_llvm_to_object,
    convert_to_llvm,
    link_executable,
    load_input_file,
    run_llvm_opt,
    run_mlir_opt,
    set_display_cmd,
    write_mlir,
)
from jsonmlir.trace import enable_trace


def print_if(
    cond: bool,
    header: str,
    path: Path,
    *,
    last_print_path: Path | None = None,
) -> None:
    if not cond:
        return
    text = path.read_text()
    print()
    print("────── " + header)
    if (
        last_print_path is not None
        and last_print_path.exists()
    ):
        import difflib

        from rich.console import Console
        from rich.syntax import Syntax

        prev_text = last_print_path.read_text()
        diff = "\n".join(
            difflib.unified_diff(
                prev_text.splitlines(),
                text.splitlines(),
                fromfile="before",
                tofile=header,
                lineterm="",
            )
        )
        if diff:
            Console().print(Syntax(diff, "diff"))
        else:
            Console().print(Syntax(text, "mlir"))
    else:
        print(text)
    print()
    if last_print_path is not None:
        last_print_path.write_text(text)

MLIR_OPT_PASSES: list[str] = [
    "--loop-invariant-code-motion",
    "--inline",
    "--cse",
    "--canonicalize",
    "--symbol-dce",
    "--mem2reg",
    "--expand-strided-metadata",
    "--normalize-memrefs",
    "--memref-expand",
    "--remove-dead-values",
    "--fold-memref-alias-ops",
    "--symbol-privatize",
]

LLVM_OPT_PASSES: list[str] = [
    "globaldce",
    "default<O3>" #O1
]

MLIR_OPT_LOWER_TO_LLVM: Sequence[str] = [
    "convert-index-to-llvm",
    "lower-affine",
    "convert-scf-to-cf",
    "expand-strided-metadata",
    "normalize-memrefs",
    "memref-expand",
    "fold-memref-alias-ops",
    "finalize-memref-to-llvm",
    "convert-cf-to-llvm",
    "convert-func-to-llvm",
    "convert-arith-to-llvm",
    "convert-math-to-llvm",
    "reconcile-unrealized-casts",
]

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    # Json -> Pydantic AST
    data = load_input_file(args.input)
    module_ast = build_sample_ast_json(data)
    return compiler(module_ast, argv)


def compiler(module_ast: ModuleJsonOp, argv: Sequence[str] | None = None) -> int:
    # Read params and configuration
    args = parse_args(argv)
    output_name = resolve_output_name(args.input, args.output_name)
    enable_trace()
    set_display_cmd(args.cmd)
    project_root = args.project_root.resolve()
    toolchain = Toolchain.discover(
        args.mlir_bin_dir,
        project_root=project_root
    )

    # Set build path
    input_path = args.input
    build_dir = project_root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    path_call       = input_path.with_suffix(".call.cpp")
    path_mlir       = build_dir / f"{output_name}.mlir"
    path_optimized  = build_dir / f"{output_name}.mlir.opt"
    path_llvm_mlir  = build_dir / f"{output_name}.llvm.mlir"
    path_llvm       = build_dir / f"{output_name}.ll"
    path_llvm_opti  = build_dir / f"{output_name}.ll.opt"
    path_object     = input_path.with_suffix(".o")
    path_runnable   = input_path.with_suffix(".out")
    path_last_print = build_dir / f"{output_name}.last.ir"
    if not args.show_diff:
        path_last_print = None

    # Pydantic -> MLIR (bindings Python)
    if args.tree:
        print()
        print("────── Python AST")
        enable_trace(True)
    with Context(), Location.unknown():
        module = Module.create()
        with InsertionPoint(module.body):
            module_ast.codegen()

        # Print
        write_mlir(module, path_mlir)
    print_if(
        args.mlir,
        "MLIR (codegen)",
        path_mlir,
    )
    if path_last_print is not None:
        path_last_print.write_text(path_mlir.read_text())

    print_if(
        args.mlir,
        "MLIR",
        path_mlir,
        last_print_path=path_last_print,
    )

    # MLIR passes
    run_mlir_opt(
        toolchain,
        path_mlir,
        path_optimized,
        MLIR_OPT_PASSES,
        display_passes=args.mlir_passes
    )
    print_if(
        args.mlir_opti,
        "Optimized MLIR",
        path_optimized,
        last_print_path=path_last_print,
    )

    # mlir -> llvm mlir
    passes = f"builtin.module({','.join(MLIR_OPT_LOWER_TO_LLVM)})"
    run_mlir_opt(
        toolchain,
        path_optimized,
        path_llvm_mlir,
        [f"--pass-pipeline={passes}"]
    )
    print_if(
        args.mlir_llvm,
        "MLIR LLVM dialect",
        path_llvm_mlir,
        last_print_path=path_last_print,
    )

    # llvm mlir -> llvm
    convert_to_llvm(
        toolchain,
        path_llvm_mlir,
        path_llvm
    )
    print_if(
        args.llvm,
        "LLVM",
        path_llvm,
        last_print_path=path_last_print,
    )

    # llvm -> llvm opti
    run_llvm_opt(
        toolchain,
        path_llvm,
        path_llvm_opti,
        LLVM_OPT_PASSES
    )
    print_if(
        args.llvm_opti,
        "LLVM opti",
        path_llvm,
        last_print_path=path_last_print,
    )


    # llvm -> objet relocatable (.o)
    compile_llvm_to_object(
        toolchain,
        path_llvm_opti,
        path_object,
    )

    if args.link:
        link_executable(
            toolchain,
            path_call,
            path_object,
            path_runnable,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
