```shell
# Clone LLVM project with release tag
LLVM_PROJECT_PATH=~/llvm-project
git clone --depth=1 https://github.com/llvm/llvm-project --branch llvmorg-22.1.8 $LLVM_PROJECT_PATH


# Setup python env
uv python install 3.13
uv venv ~/.venv/mlirdev --python 3.13
source ~/.venv/mlirdev/bin/activate
uv pip install --upgrade pip
uv pip install -r "$LLVM_PROJECT_PATH/mlir/python/requirements.txt"

# Build python bindings
sudo dnf install ccache ninja-build lld
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

# check-mlir-python have ~4 failing tests out of 100; you may check the result manually
ninja -C "$LLVM_PROJECT_PATH/build" check-mlir-python || true

# Add interface using package pth
MLIR_CORE="$LLVM_PROJECT_PATH/build/tools/mlir/python_packages/mlir_core"
echo "$MLIR_CORE" > "$VIRTUAL_ENV/lib/python3.13/site-packages/mlir_core.pth"


# Test installation
python -c "import mlir.ir; print('OK')"
# ou, sans activer le venv :
# uv run python -c "import mlir.ir; print('OK')"
```

Doc : `mlir/docs/Bindings/Python.md`.
