# Installation

## Docker

### Image (once, long build: 1–2 h)

```bash
git clone git@github.com:LouisMaxHa/jsonMLIR.git
cd jsonMLIR/

# From the repository root
docker build -t jsonmlir .       # Build
export PATH="$(pwd)/bin:$PATH"   # Expose jsonmlir wrapper
```

The wrapper:
- Mounts the current directory on `/workspace`
- Mounts the source repository (editable code without need to rebuild)
- Only rebuilds the image if the `Dockerfile` or `pyproject.toml` has changed

```bash
# Tests (from the jsonMLIR clone) - theses are equivalents
jsonmlir
jsonmlir tests/run_tests.py -j 8
jsonmlir python tests/run_tests.py -j 8

# Generate a library from a Python DSL script
jsonmlir examples/python_max/main.py

# Generate a library from JSON/YAML (package CLI)
jsonmlir examples/somme/main.json -A

# From your project (e.g. microhydro/build/)
jsonmlir ../src/librairie.py -TC

# Interactive shell
jsonmlir bash

# Rebuild the image manually
jsonmlir build-image
```

Manual equivalent of `jsonmlir myCode/myLib.py -TC`:

```bash
docker run --rm \
  -v "$(pwd):/workspace" \
  -v "/path/to/jsonMLIR:/opt/jsonMLIR" \
  -w /workspace \
  jsonmlir python myCode/myLib.py -TC
```

Manual equivalent for a JSON file:

```bash
docker run --rm \
  -v "$(pwd):/workspace" \
  -v "/path/to/jsonMLIR:/opt/jsonMLIR" \
  -w /workspace \
  jsonmlir jsonmlir examples/somme/main.json -A
```

> **Note:** the image does not include `examples/`. Any run of application code or examples goes through the host repository mount (wrapper or explicit `-v`).

## Manual installation

If you run into issues, you can also look at the Dockerfile.

```shell
# Python environment
uv python install 3.13
uv venv ~/.venv/mlirdev --python 3.13
source ~/.venv/mlirdev/bin/activate
uv pip install --upgrade pip

# Clone LLVM
LLVM_PROJECT_PATH=~/llvm-project
git clone --depth=1 https://github.com/llvm/llvm-project --branch llvmorg-22.1.8 $LLVM_PROJECT_PATH
uv pip install -r "$LLVM_PROJECT_PATH/mlir/python/requirements.txt"

# Build the Python bindings
sudo dnf install ccache ninja-build lld clang
cmake -G Ninja -S "$LLVM_PROJECT_PATH/llvm" -B "$LLVM_PROJECT_PATH/build" \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DLLVM_BUILD_EXAMPLES=ON \
  -DLLVM_TARGETS_TO_BUILD="Native;NVPTX;AMDGPU" \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
  -DPython3_EXECUTABLE="$VIRTUAL_ENV/bin/python" \
  -DPython_EXECUTABLE="$VIRTUAL_ENV/bin/python" \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DLLVM_ENABLE_LLD=ON

cmake --build "$LLVM_PROJECT_PATH/build"
export PATH="$LLVM_PROJECT_PATH/build/bin:$PATH"

# check-mlir-python: ~4 failing tests out of ~100; check manually if needed
ninja -C "$LLVM_PROJECT_PATH/build" check-mlir-python || true

# Register the MLIR package in the venv
MLIR_CORE="$LLVM_PROJECT_PATH/build/tools/mlir/python_packages/mlir_core"
echo "$MLIR_CORE" > "$VIRTUAL_ENV/lib/python3.13/site-packages/mlir_core.pth"
uv run python -c "import mlir.ir; print('OK')"

# Run the tests
uv run python tests/run_tests.py -j 8
```
