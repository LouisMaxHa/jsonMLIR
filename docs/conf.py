"""Sphinx configuration for the jsonMLIR documentation."""

from pathlib import Path
import sys
from inspect import cleandoc, getdoc
from typing import Any

from docutils import nodes


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

project = "jsonMLIR"
copyright = "2026, jsonMLIR contributors"
author = "jsonMLIR contributors"
try:
    from jsonmlir import __version__

    release = __version__
except ImportError:
    release = "0.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

# The MLIR Python bindings are supplied by the LLVM build and are not a PyPI
# dependency. Mocking them keeps API documentation builds lightweight.
autodoc_mock_imports = ["mlir"]
autodoc_default_options = {
    "exclude-members": "codegen,model_config,get_type,get_memref_type",
    "members": True,
    "member-order": "bysource",
    "show-inheritance": True,
}
autodoc_typehints = "description"
autodoc_type_aliases = {
    "TyNode": "jsonmlir.variables.ty.ty.TyNode",
}
autodoc_inherit_docstrings = True
autosummary_generate = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "slides"]

html_theme = "furo"
html_title = "jsonMLIR documentation"
add_module_names = False


def _document_dsl_from_operation(
    app: Any,
    what: str,
    name: str,
    obj: Any,
    options: Any,
    lines: list[str],
) -> None:
    """Use the corresponding operation model as the DSL function's API docs."""
    del app, options
    prefix = "jsonmlir.operations.dsl."
    if what != "function" or not name.startswith(prefix):
        return

    module = sys.modules.get(getattr(obj, "__module__", ""))
    if module is None:
        return

    operation_name = getattr(obj, "__annotations__", {}).get("return")
    if not isinstance(operation_name, str):
        return

    operation = getattr(module, operation_name, None)
    if operation is None:
        return

    docstring = getdoc(operation)
    if docstring is not None:
        lines[:] = cleandoc(docstring).splitlines()


def _shorten_type_alias_fields(app: Any, doctree: nodes.document, docname: str) -> None:
    """Keep expanded Pydantic type aliases readable in autodoc parameters."""
    del app, docname
    alias = "TypeAliasForwardRef('jsonmlir.variables.ty.ty.TyNode')"
    for field in doctree.findall(nodes.field):
        body = field.next_node(nodes.field_body)
        if body is None or alias not in body.astext():
            continue
        text = body.astext().replace(alias, "TyNode")
        body.clear()
        body += nodes.paragraph(text=text)


def setup(app: Any) -> dict[str, str]:
    """Register the DSL-to-operation documentation bridge."""
    app.connect("autodoc-process-docstring", _document_dsl_from_operation)
    app.connect("doctree-resolved", _shorten_type_alias_fields)
    return {"version": "1"}
