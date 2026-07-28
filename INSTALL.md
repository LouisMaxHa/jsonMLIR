```shell
# Clone LLVM project with release tag
git clone --depth=1 https://github.com/llvm/llvm-project --branch llvmorg-22.1.8 ~/llvm-project


# Setup python env
uv python install 3.13
uv venv ~/.venv/mlirdev --python 3.13
source ~/.venv/mlirdev/bin/activate

uv pip install --upgrade pip
uv pip install -r ~/llvm-project/mlir/python/requirements.txt

# Build python bindings
mkdir ~/llvm-project/build
cd ~/llvm-project/build
sudo dnf install ccache ninja-build ldd
cmake -G Ninja ../llvm \
   -DLLVM_ENABLE_PROJECTS=mlir \
   -DLLVM_BUILD_EXAMPLES=ON \
   -DLLVM_TARGETS_TO_BUILD="Native;NVPTX;AMDGPU" \
   -DCMAKE_BUILD_TYPE=Release \
   -DLLVM_ENABLE_ASSERTIONS=ON \
   -DCMAKE_C_COMPILER=clang -DMLIR_ENABLE_BINDINGS_PYTHON=ON -DCMAKE_CXX_COMPILER=clang++ -DLLVM_ENABLE_LLD=ON

make
ninja check-mlir-python

# Export path
export PATH=~/llvm-project/build/bin:$PATH  
MLIR_CORE="~/llvm-project/build/tools/mlir/python_packages/mlir_core"
SITE_PACKAGES="$(python -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"
echo "$MLIR_CORE" > "$SITE_PACKAGES/mlir_core.pth"

# Test installation
python -c "import mlir.ir; print('OK')"
```

Doc : `mlir/docs/Bindings/Python.md`.
