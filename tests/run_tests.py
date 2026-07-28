"""End-to-end runner for JSON → MLIR → native executable examples."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

EXPECT_PATTERN = re.compile(
    r"EXPECT(?:ED)?.*? '([^']*)'.*?'([^']*)'",
    re.IGNORECASE,
)

console = Console()
_print_lock = threading.Lock()


class ResultStats(Enum):
    OK = "Ok"
    ERROR = "Error"   # Crash of the program
    FAILED = "Failed" # Test failed


_STATUS_STYLES: dict[ResultStats, str] = {
    ResultStats.OK: "bold green",
    ResultStats.ERROR: "bold red",
    ResultStats.FAILED: "bold red",
}


@dataclass
class ResultInfo:
    name: str
    status: ResultStats
    message: str
    elapsed_s: float = 0.0


def discover_examples(project_root: Path) -> list[Path]:
    """Return main.json or main.py paths for each example subdirectory.

    Directories with a ``main.json`` are compiled via the JSON pipeline.
    Directories that only have a ``main.py`` (no ``main.json``) use the Python
    DSL to generate the binary directly.
    """
    examples_dir = project_root / "examples"
    paths: list[Path] = []
    for child in sorted(examples_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "main.json").is_file():
            paths.append(child / "main.json")
        elif (child / "main.py").is_file():
            paths.append(child / "main.py")
    return paths


def _parse_expectations(stdout: str) -> tuple[list[tuple[str, str]], int]:
    """Return mismatches parsed from stdout."""
    mismatches: list[tuple[str, str]] = []
    n_tests = 0
    for line in stdout.splitlines():
        match = EXPECT_PATTERN.search(line)
        if match is None:
            continue
        expected, got = match.group(1), match.group(2)
        if expected != got:
            mismatches.append((expected, got))
        n_tests += 1
    return (mismatches, n_tests)


def _compile_example(
    input_path: Path,
    project_root: Path,
) -> subprocess.CompletedProcess[str] | None:
    """Compile an example in a subprocess for process-level isolation."""
    output_name = input_path.parent.name
    if input_path.suffix == ".py":
        cmd = [
            sys.executable,
            str(input_path),
            "--project-root",
            str(project_root),
            "--output-name",
            output_name,
        ]
    else:
        cmd = [
            sys.executable,
            "-m",
            "xdsljson.pipeline.cli",
            str(input_path),
            "--project-root",
            str(project_root),
            "--output-name",
            output_name,
            "--link",
        ]
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except Exception:
        return None


def run_example(input_path: Path, project_root: Path) -> ResultInfo:
    """Compile and run an example, then check EXPECT lines.

    Accepts either a ``main.json`` (JSON pipeline) or a ``main.py`` (Python
    DSL pipeline) as *input_path*.
    """
    start = time.perf_counter()
    name = input_path.parent.name
    project_root = project_root.resolve()
    input_path = input_path.resolve()
    file_runnable = input_path.with_suffix(".out")

    proc_compile = _compile_example(input_path, project_root)
    if proc_compile is None:
        return ResultInfo(
            name=name,
            status=ResultStats.ERROR,
            message="compilation subprocess failed to start",
            elapsed_s=time.perf_counter() - start,
        )

    if proc_compile.returncode != 0:
        rc = proc_compile.returncode
        detail = proc_compile.stderr.strip() or f"exit code {rc}"
        return ResultInfo(
            name=name,
            status=ResultStats.ERROR,
            message=detail,
            elapsed_s=time.perf_counter() - start,
        )

    # Run file
    try:
        proc = subprocess.run(
            [str(file_runnable)],
            capture_output=True,
            text=True,
            cwd=str(input_path.parent),
            timeout=30,
            check=False,
        )

    # Can't run program
    except OSError as exc:
        return ResultInfo(
            name=name,
            status=ResultStats.ERROR,
            message=str(exc),
            elapsed_s=time.perf_counter() - start,
        )

    # Program crash
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit code {proc.returncode}"
        return ResultInfo(
            name=name,
            status=ResultStats.ERROR,
            message=detail,
            elapsed_s=time.perf_counter() - start,
        )

    # Check tests
    mismatches, n_tests = _parse_expectations(proc.stdout)
    if mismatches:
        details = ", ".join(f"'{exp}' != '{got}'" for exp, got in mismatches)
        return ResultInfo(
            name=name,
            status=ResultStats.FAILED,
            message=details,
            elapsed_s=time.perf_counter() - start,
        )

    # Ok
    return ResultInfo(
        name=name,
        status=ResultStats.OK,
        message=f"{n_tests}/{n_tests}",
        elapsed_s=time.perf_counter() - start,
    )


def _format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"


def print_summary(results: list[ResultInfo]) -> None:
    """Print a colored summary table with timing benchmark."""
    if not results:
        return

    table = Table(title="Summary", show_lines=True)
    table.add_column("Example", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Duration", justify="right", style="magenta")
    table.add_column("Detail")

    passed = 0
    total_time = 0.0
    slowest = max(results, key=lambda r: r.elapsed_s)

    for result in results:
        total_time += result.elapsed_s
        if result.status == ResultStats.OK:
            passed += 1

        detail: str | Text = result.message
        if result.status != ResultStats.OK:
            detail = Text(result.message, style="red")

        table.add_row(
            result.name,
            Text(result.status.value, style=_STATUS_STYLES[result.status]),
            _format_duration(result.elapsed_s),
            detail,
        )

    console.print()
    console.print(table)

    failed = len(results) - passed
    summary_style = "bold green" if failed == 0 else "bold red"
    console.print(
        f"\n[bold]Benchmark[/bold]: "
        f"[{summary_style}]{passed}/{len(results)} passed[/] "
        f"— total [magenta]{_format_duration(total_time)}[/] "
        f"— slowest [yellow]{slowest.name}[/] "
        f"([magenta]{_format_duration(slowest.elapsed_s)}[/])"
    )


def _print_progress(infos: ResultInfo) -> None:
    with _print_lock:
        console.print(
            "Testing [cyan]{:.<40}".format(infos.name + "[/]"),
            end=" ",
        )
        if infos.status == ResultStats.OK:
            console.print(infos.message)
        else:
            console.print("")


def run_all_examples(
    project_root: Path | None = None,
    *,
    jobs: int | None = None,
) -> list[ResultInfo]:
    """Run all examples and print the summary."""
    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    paths = discover_examples(root)
    workers = jobs if jobs is not None else (os.cpu_count() or 4)

    console.print(
        f"[bold]Running {len(paths)} examples[/] from [cyan]{root / 'examples'}[/] "
        f"([magenta]{workers} worker{'s' if workers != 1 else ''}[/])\n"
    )

    results: list[ResultInfo] = []
    if workers <= 1:
        for path in paths:
            infos = run_example(path, root)
            _print_progress(infos)
            results.append(infos)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_path = {
                executor.submit(run_example, path, root): path for path in paths
            }
            for future in as_completed(future_to_path):
                infos = future.result()
                _print_progress(infos)
                results.append(infos)

        results.sort(key=lambda result: result.name)

    print_summary(results)
    return results


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    default_jobs = os.cpu_count() or 4
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=default_jobs,
        metavar="N",
        help=f"number of parallel workers (default: {default_jobs})",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    results = run_all_examples(jobs=args.jobs)
    failed = [r for r in results if r.status != ResultStats.OK]
    sys.exit(1 if failed else 0)
