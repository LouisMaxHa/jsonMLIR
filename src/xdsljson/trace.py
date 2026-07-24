"""Codegen trace displayed as a tree via Rich."""

from __future__ import annotations

import contextvars
import inspect
import os
from collections.abc import Callable
from functools import wraps
from string import Formatter
from typing import Any, cast

from mlir.ir import Block, InsertionPoint
from rich.console import Console
from rich.tree import Tree

_console = Console()
_tree_root: contextvars.ContextVar[Tree | None] = contextvars.ContextVar(
    "tree_root", default=None
)
_tree_stack: contextvars.ContextVar[list[Tree]] = contextvars.ContextVar(
    "tree_stack", default=[]
)
_trace_enabled: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "trace_enabled", default=False
)

_TRACE_ENV_VALUES = {"1", "true", "yes"}


def is_trace_enabled() -> bool:
    return _trace_enabled.get()


def enable_trace(enabled: bool = True) -> None:
    _trace_enabled.set(enabled)


class _TraceFormatter(Formatter):
    def format_field(self, value: Any, format_spec: str) -> str:
        if format_spec:
            return format(value, format_spec)
        return _format_arg(value)


def _format_arg(value: Any) -> str:
    if isinstance(value, InsertionPoint):
        return "<InsertionPoint ... >"
    if isinstance(value, Block):
        return "<Block ... >"
    if isinstance(value, tuple):
        items = cast(tuple[Any, ...], value)
        return f"({', '.join(_format_arg(v) for v in items)})"
    if isinstance(value, list):
        items = cast(list[Any], value)
        return f"[{', '.join(_format_arg(v) for v in items)}]"
    return repr(value)


def _resolve_label(label: str, arguments: dict[str, Any]) -> str:
    try:
        return _TraceFormatter().vformat(label, (), arguments)
    except (KeyError, AttributeError, IndexError, ValueError):
        return label


def _bind_arguments(
    fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    sig = inspect.signature(fn)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _bind_context(
    fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, str]:
    return {name: _format_arg(val) for name, val in _bind_arguments(fn, args, kwargs).items()}


def _current_node() -> Tree | None:
    stack = _tree_stack.get()
    if not stack:
        return None
    return stack[-1]


def trace_note(message: str) -> None:
    """Add a note under the current node of the trace tree.

    Example in a ``codegen``::

        trace_note("initializing arguments")
    """
    if not _trace_enabled.get():
        return
    node = _current_node()
    if node is None:
        return
    node.add(f"[dim italic]{message}[/]")


def _tree_enter(resolved: str, ctx: dict[str, str], *, display_entry: bool) -> Tree:
    stack = list(_tree_stack.get())
    if not stack:
        node = Tree(f"[bold cyan]{resolved}[/]")
        _tree_root.set(node)
        stack = [node]
    else:
        node = stack[-1].add(resolved)
        stack.append(node)
    _tree_stack.set(stack)

    if display_entry:
        node._entry_ctx = ctx  # type: ignore[attr-defined]
    return node


def _format_exit_label(
    resolved: str,
    result: Any,
    *,
    error: bool,
    entry_ctx: dict[str, str] | None,
    skip_result: bool = False,
) -> str:
    if error:
        return f"[bold red]✗ {resolved}[/]"
    if skip_result:
        main = resolved
    else:
        main = f"{resolved}  [green]← {_format_arg(result)}[/]"
    if not entry_ctx:
        return main
    args_lines = "\n".join(
        f"│       - [dim]{name}[/] = {formatted}"
        for name, formatted in entry_ctx.items()
    )
    return f"{main}\n{args_lines}"


def _tree_exit(
    node: Tree,
    resolved: str,
    result: Any,
    *,
    error: bool = False,
    skip_result: bool = False,
) -> None:
    entry_ctx = getattr(node, "_entry_ctx", None)
    node.label = _format_exit_label(
        resolved, result, error=error, entry_ctx=entry_ctx, skip_result=skip_result
    )

    stack = list(_tree_stack.get())
    stack.pop()
    _tree_stack.set(stack)

    if not stack:
        root = _tree_root.get()
        if root is not None:
            _console.print(root)
            _tree_root.set(None)


def trace_step(label: str, *, display_entry: bool = False):
    """Trace a function or block and display the call as a tree.

    Decorator::

        @trace_step("ConstOp: val={self.val}")
        def codegen(self) -> ValNode: ...

    Warning: avoid labels that parse as a call to the decorated method's own
    class (e.g. ``"ConstOp({self.val})"``): with ``enableExperimentalFeatures``,
    pyright evaluates such strings speculatively and crashes with an infinite
    recursion (RangeError: Maximum call stack size exceeded). See PoC/.

    Context manager::

        with trace_step("Loading args"):
            ...

    label : str.format() template — parameter and attribute names
            (e.g. ``ConstOp: val={self.val}``, ``from_val type={type}``).
    display_entry : add input parameters as child nodes.
    """

    class _TraceStep:
        def __init__(self) -> None:
            self._node: Tree | None = None
            self._resolved = label

        def __enter__(self) -> _TraceStep:
            if not _trace_enabled.get():
                return self
            self._node = _tree_enter(self._resolved, {}, display_entry=display_entry)
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
            if not _trace_enabled.get() or self._node is None:
                return False
            _tree_exit(
                self._node,
                self._resolved,
                None,
                error=exc_type is not None,
                skip_result=True,
            )
            return False

        def __call__(self, fn: Callable[..., Any]) -> Callable[..., Any]:
            @wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not _trace_enabled.get():
                    return fn(*args, **kwargs)

                ctx = _bind_context(fn, args, kwargs)
                arguments = _bind_arguments(fn, args, kwargs)
                resolved = _resolve_label(label, arguments)
                node = _tree_enter(resolved, ctx, display_entry=display_entry)
                try:
                    result = fn(*args, **kwargs)
                    _tree_exit(node, resolved, result)
                    return result
                except Exception:
                    _tree_exit(node, resolved, None, error=True)
                    raise

            return wrapper

    return _TraceStep()


def configure_trace() -> None:
    """Enable tracing if XDSLJSON_TRACE is set to 1, true, or yes."""
    if os.environ.get("XDSLJSON_TRACE", "").lower() in _TRACE_ENV_VALUES:
        enable_trace(True)
