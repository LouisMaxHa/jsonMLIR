"""jsonMLIR — a JSON/YAML → MLIR → LLVM compiler.

The package version is derived from the repository by ``hatch-vcs`` and recorded
in the installed distribution metadata. When the package is imported from an
uninstalled source checkout, a fallback value is used.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("jsonmlir")
except PackageNotFoundError:  # pragma: no cover - not installed
    __version__ = "0.0.0"

__all__ = ["__version__"]
