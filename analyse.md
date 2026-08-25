# jsonMLIR — Global & Technical Review

This document provides a global and technical review of the **jsonMLIR** repository.
It highlights architectural issues, code smells, refactoring advice, and missing
best practices, with `file:line` references.

> Review date: 2026-08-25 · Branch: `ts-ast-jsonschema`

---

## 1. Project overview

jsonMLIR is a **JSON/YAML → MLIR → LLVM → native library** compiler. It takes a
JSON description of functions (scalars, arrays, pointers, structs, SOA buffers)
and generates a shared library that can be called from C++ without writing an
MLIR front-end.

**Pipeline** (see `src/jsonmlir/pipeline/compiler.py`):

```
JSON/YAML/Python DSL
  → Pydantic AST (ModuleJsonOp / *Op nodes)
  → MLIR codegen (Python mlir bindings)
  → mlir-opt (MLIR passes)
  → mlir-opt (lower to LLVM dialect)
  → mlir-translate (LLVM IR)
  → opt (LLVM passes)
  → llc (object file)
  → clang++ (link with C++ caller)
```

A secondary toolchain (`scripts/generate_ts_ast.py` + `ts-ast/` submodule)
exports the Pydantic AST contract as JSON Schema, then generates TypeScript
interfaces for a frontend DSL.

## 2. Architecture

- **`operations/`** — Pydantic AST nodes (`*Op`) with a `codegen()` method.
  Discriminated union `BaseValue` on the `"op"` field.
- **`variables/ty/`** — Type nodes (`TyScalar`, `TyMemref`, `TyStruct`, …),
  discriminated on the `"type"` field.
- **`variables/val/`** — Runtime value wrappers (SSA + memory address),
  implementing `load` / `store` / `get_SSA`.
- **`variables/`** — `memory.py` (global registries), `factory.py` (type→val),
  `var.py` (name↔instance binding).
- **`utils/`** — Trace tree, SSA helpers, scalar enums, bare-pointer bridge.
- **`pipeline/`** — CLI, toolchain discovery, command orchestration.

### Strengths

- Clean separation between the AST (operations), the type system (`ty`), and the
  runtime value semantics (`val`).
- Discriminated unions with Pydantic give a single-source-of-truth contract for
  JSON, which is re-exported to TypeScript.
- Excellent tracing/debugging UX: `trace_step`/`trace_note` build a Rich tree of
  the whole codegen, and `--show-diff` prints colored IR diffs between stages.
- The test harness for examples (`tests/run_tests.py`) is genuinely useful and
  parallelized.

---

## 3. Critical issues

### 3.1 Packaging — missing top-level `__init__.py`

`src/jsonmlir/__init__.py` **does not exist**, while every subpackage
(`operations/`, `variables/`, `pipeline/`, `utils/`) has one. With
`[tool.hatch.build.targets.wheel] packages = ["src/jsonmlir"]`
(`pyproject.toml:30`), the wheel build is fragile: `jsonmlir` becomes a
PEP-420 namespace package, and implicit relative imports / package data can
break. Tests only pass because `conftest.py` manipulates `sys.path`.

**Fix:** add a minimal `src/jsonmlir/__init__.py` (with `__version__` from
`hatch-vcs`) and verify `uv build` produces a working wheel.

### 3.2 Global mutable state as the core design

Codegen state lives in **module-level mutable dicts** (`variables/memory.py:26-28`):

```python
structs_type: dict[str, STRUCTS_TYPE] = {}
variables_heap: dict[str, ValNode] = {}
functions_registry: dict[str, FunctionSignature] = {}
```

Plus `utils/ssa_val.py:16` `const_heap`, and the unbounded
`utils/discard_builder.py` `_discard_modules` list.

Problems:

- **Not re-entrant / not thread-safe.** Two compilations in the same process
  (tests, a future API server) clobber each other. State is cleared ad hoc in
  `ModuleJsonOp.codegen` (`op_module.py:31-32`) and `FunctionOp.codegen`
  (`op_function.py:29-30`), so any path that skips the module root leaks.
- **`discard_builder` leaks one MLIR `Module` per call** forever
  (deliberately kept alive, but a long-running process grows unboundedly).
- `availables_functions = {}` (`op_function.py:20`) is an **unused** leftover
  duplicate of `functions_registry`.

**Fix:** introduce a `CodegenContext`/`Session` object (function-scoped heap,
module-scoped registries, const cache) threaded through `codegen()` — or at
minimum a `contextvars.ContextVar` holding a per-compilation state. This is the
single most impactful refactoring for correctness and testability.

### 3.3 `assert`-based validation on user input

Runtime checks use bare `assert` everywhere (compilers run with `-O`; asserts
are stripped): `op_alloca.py:30`, `op_alloc.py:30`, `op_set.py:32-35`,
`val_buffer.py:98`, `val_struct.py:118`, `val_memref.py:45`, `val_scalar.py:22`,
etc. Under `python -O` (or PyInstaller-packaged binaries) these disappear and
invalid JSON produces **garbage IR or segfaults** instead of clean errors.

**Fix:** move all input validation into Pydantic validators / `field_validator`
(which run regardless of `-O`), and keep asserts only for internal invariants.

### 3.4 Exception abuse and copy-paste errors

- `from sqlite3 import NotSupportedError` (`variables/val/val_memref.py:4,53`) —
  a SQLite exception raised for an MLIR type error.
- `from decimal import InvalidOperation` (`variables/val/val_SOA.py:4,60`) —
  wrong module **and** a copy-pasted message: *"ValScalar don't have SSA
  equivalent"* inside `ValSOA`, with typos ("attribut", "consumming" at lines
  53, 75, 90).
- `utils/same_types.py:28` — *"Missmatch detected at indice"* (typos + no return
  annotation + trailing space `) :`).
- `run_command` (`commands.py:151`) calls `exit(1)` instead of raising — makes
  the library unusable programmatically and hard to test.
- `load_input_file` returns an `int` (`1`) on error but is typed `-> Any`
  (`commands.py:22-26`) — the caller then feeds an int to Pydantic.

**Fix:** define a small exception hierarchy (`JsonMLIRValidationError`,
`JsonMLIRToolchainError`, `CodegenError`) and raise consistently; remove stray
`print('hey')` debug statements in `compiler.py:107` and `cli.py:180`.

### 3.5 Duplicated logic

- `enum_scalars.py` repeats the enum-case lists **three times** (`byte_size`,
  `get_kind`, `get_type`) — adding a scalar means editing three `match` blocks
  and they can drift (e.g. `f80`/`f128` have a `byte_size` but
  `get_type()` raises — `enum_scalars.py:88-90`).
- `ty.py` defines the same 7-member type union **three times**
  (lines 70-82, 110-121, 134-137).
- `val_ptr`/`val_scalar` share the alloca→store→load init pattern and a
  verbatim multi-line assert message.
- Double lookups: `struct.FIELDS[field_name]` twice in `val_struct.py:116-117`;
  `get_size()` recomputed in `val_buffer.build_view` (lines 125 and 134).
- `ValMemref.init_from` has two **identical** `match` branches (`TyMemref` and
  `TySSA`, `val_memref.py:47-51`).
- `parseTyOrScalar` in `ts-ast/manual.ts` is a no-op returning its input.

### 3.6 Fragile codegen tooling

- `scripts/generate_ts_ast.py` **imports `tests.conftest`** to install MLIR
  stubs — a production script depending on the test package. It will break if
  `tests/` is excluded from a wheel.
- `patch_schema_ts` does **brittle exact-string replacement** of generated
  TypeScript — silently no-ops if `json2ts` output changes formatting.
- `compiler.py:88-102` hardcodes the pass pipeline as string lists, including an
  inline comment `"default<O1>" #O1` (`compiler.py:85`).

### 3.7 Type-safety / typing gaps

- `reportAssertAlwaysTrue` and strict pyright are configured (`pyproject.toml:44-56`)
  but the codebase still relies on runtime asserts for narrowing
  (`var.py:45-53` `match (given_type is None, saved_type is None)` with asserts
  to convince pyright).
- `ValNode.get_ty()` is typed `-> T` but several classes are only `ValNode[...]`,
  forcing casts/`Any` downstream.
- `StructField.type: Any` (`struct_field.py:14`) — the pydantic union is avoided
  for circular imports; a `ForwardRef` + `model_rebuild` would restore typing.
- `ValBuffer.get_size()` returns `int | Value` — every caller must branch.
- **The MLIR stubs in `conftest.py` make any typo pass silently**: `mlir.ir.Typo`
  auto-creates a stub module instead of failing. Schema-only tests are fine, but
  nothing stops the stubs from masking real MLIR API misuse.

### 3.8 Security & hygiene

- `mkdocs.yml:100` loads **polyfill.io** (`https://polyfill.io/v3/...`) — the
  domain was sold in 2024 and is flagged for serving malicious content. Remove it.
- `.vscode/launch.json` leaks a **hardcoded personal path** from a *different*
  repo (`/home/harterl/git/modane-xdsl/...`) — clearly committed by accident.
- `.gitmodules` uses an **SSH URL** (`git@github.com:...`) for the `ts-ast`
  submodule — clone fails for contributors without SSH keys.
- `renovate.json:11-13` enables `nix` for a pure Python project (dead config) and
  duplicates `semanticCommitType`.
- Committed build/test artifacts pollute the working tree (ignored but present):
  `examples/*.o`, `*.out`, `__pycache__/`, `build/`, `docs/arcane/*.o`.
  `.gitignore` is otherwise effective.

### 3.9 Docs & CI mismatches

- **Broken mkdocs nav** (`mkdocs.yml:22-24`): points to `index.md` and
  `reference.md` which **do not exist** in `docs/`.
- **Repo URL inconsistency**: `mkdocs.yml` / `README.md` use
  `Louis-max-H/jsonMLIR`, while `INSTALL.md` and the submodule use `LouisMaxHa`.
- Version drift: CI uses **Python 3.12** (`ts-ast-schema.yml:27`), Dockerfile and
  `.python-version` use **3.13**, and committed `.pyc` files show **3.14** locally.
- `docs/optimize_demo.sh` is an **empty 0-byte file**.
- There is **no CI job** for `make check` (ruff), `pyright`, or `pytest` on the
  main pipeline — only the `ts-ast` schema workflow exists. A regression can be
  merged without any automated check.

---

## 4. Refactoring advice

### 4.1 Thread a `CodegenContext` through codegen (priority: high)

Replace `memory.py` globals with a context object created per module:

```python
@dataclass
class CodegenContext:
    structs: dict[str, STRUCTS_TYPE] = field(default_factory=dict)
    functions: dict[str, FunctionSignature] = field(default_factory=dict)
    heap: dict[str, ValNode] = field(default_factory=dict)
    consts: dict[tuple, list[Value]] = field(default_factory=dict)
```

Have `OpNode.codegen(ctx)` take it explicitly (or store it in a
`contextvars.ContextVar` with `discard_builder` cleaned up on exit). This fixes
re-entrancy, the `const_heap` leak, and makes unit tests trivial.

### 4.2 Introduce a proper error hierarchy (priority: high)

```python
class JsonMLIRError(Exception): ...
class ValidationError(JsonMLIRError): ...      # bad user JSON
class CodegenError(JsonMLIRError): ...         # internal MLIR issues
class ToolchainError(JsonMLIRError): ...       # missing binaries, subprocess fails
```

Replace `sqlite3.NotSupportedError`, `decimal.InvalidOperation`, `exit(1)`/`sys.exit`
in `commands.py`, and the bare `raise Exception` in `var.py:42`.

### 4.3 Move validation into Pydantic (priority: high)

Add `field_validator`s for:
- `SetOp`: index count vs. `var.indices`; value/var type compatibility
  (`op_set.py:31-35`).
- `AllocOp`/`AllocaOp`: name collision, size list (`op_alloc.py:30`).
- `StructField`: offset/size divisibility (`val_struct.py:118`).
- `ConstOp`: float into integer scalar (`op_constant.py`).

Asserts then remain only for internal invariants that cannot be triggered by user
input.

### 4.4 Make the compiler stateful instead of functional-static (priority: medium)

`compiler()` (`compiler.py:114`) is a long sequential function with 10+ derived
paths. Consider a `Pipeline` class or a dataclass of `(toolchain, paths, flags)`
so stages are individually testable and the diff/print logic
(`print_if` with `last_print_path` state) is encapsulated. Move the
`if TYPE_CHECKING:`-style conditional imports (`difflib`, `rich`) at
`compiler.py:43-47` to module top.

### 4.5 Deduplicate the type-system unions (priority: medium)

Generate the 7-type union once (single source) in `ty.py` and reuse it for
`TyNode`, `TyNested`, and the lazy `TypeAdapter`, instead of the three copies.
Also collapse the duplicated `match` tables in `enum_scalars.py` into data-driven
tables (`{"i64": (ScalarFamily.int, 8, IntegerType.get_signless(64)), ...}`).

### 4.6 Harden the toolchain (priority: medium)

- Replace string-replacement patching in `scripts/generate_ts_ast.py` with
  `json-schema-to-typescript` options (or a real transformer), and drop the
  `tests.conftest` import (put MLIR stubs in a dedicated support module).
- Raise instead of `exit(1)` in `run_command`, and include stderr/stdout + the
  toolchain name in a structured exception.
- Type `load_input_file` properly (`-> dict | list | ... | NoReturn`).

### 4.7 Reduce magic strings (priority: low)

- `"*"` dereference marker in `val_ptr._load` → a named constant.
- `PRINT_INT_SYMBOL` exists already; extend the pattern.
- `op_define_struct.py:16` uses `op: Literal["define struct"] = "define struct"`
  (with a space) — inconsistent with all other ops; rename to `define_struct`.

---

## 5. Missing best practices

| Area | What is missing | Suggested action |
|---|---|---|
| CI | No lint/typecheck/test job for the Python pipeline | Add a GitHub Actions job running `make check`, `pyright`, `pytest`, and the filecheck suite |
| Pre-commit | No git hooks | Add `pre-commit` (ruff, pyright, trailing-whitespace, secrets scan) |
| Coverage | `pytest --cov` configured but no gate; codegen untested without real MLIR | Add a `--cov-fail-under` gate; add pytest tests for pure-Python logic (type coercion, validation, schema) |
| Docs | Broken mkdocs nav, empty placeholder file, stale URLs | Fix nav, delete `optimize_demo.sh`, unify repo URL, remove polyfill.io |
| Security | `bandit` config exists (`pyproject.toml:79`) but never runs | Wire into CI; `gitleaks`/`trufflehog` for the leaked path class of issue |
| Repo hygiene | Leaked absolute path in `.vscode/launch.json`; committed binaries in `examples/` | Remove `launch.json` or make it relative; clean ignored artifacts; add a `clean` gitignore section |
| Reproducibility | Python version drift (3.12/3.13/3.14); no lockfile pinning MLIR build | Align versions; pin MLIR commit in `Dockerfile`/`INSTALL.md`; commit `uv.lock` |
| Contribution | No `CONTRIBUTING.md` | Document branch model (5 stale branches) and the `ts-ast` regeneration workflow |
| Error handling | Mixed French/English messages, typos, `exit()` in library code | Standardize on English; define a message glossary; add a linter for typos |
| Dependency management | `renovate.json` nix config; redundant semantic-commit settings | Clean up; enable Renovate for the `ts-ast` submodule too |
| Release | No release/versioning workflow; `dynamic = ["version"]` via hatch-vcs | Add a `gh release` / tag workflow; generate changelog |

---

## 6. Recommended priority order

1. **Packaging**: add `src/jsonmlir/__init__.py` and verify wheel builds.
2. **State**: replace global registries with a `CodegenContext`.
3. **Validation**: move user-input asserts into Pydantic validators.
4. **Errors**: proper exception hierarchy; remove `exit()`/`sys.exit` from library code.
5. **CI**: add lint/typecheck/test job for the main pipeline.
6. **Security/hygiene**: remove polyfill.io, leaked `.vscode/launch.json`, SSH
   `.gitmodules` URL; clean working-tree artifacts.
7. **Docs**: fix mkdocs nav and repo-URL inconsistency.
8. **Dedup**: collapse the triplicated unions and `enum_scalars` tables.
9. **Tooling**: de-brittle `generate_ts_ast.py`.
10. **Nice-to-have**: pre-commit hooks, coverage gate, release workflow.