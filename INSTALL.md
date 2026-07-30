# Installation

## Docker

```bash
# Depuis la racine du dépôt (build long : 1–2 h, plusieurs Go)
docker build -t jsonmlir .
docker run --rm jsonmlir python -c "import mlir.ir; print('OK')"


# Taille (lisible) et résumé
docker images jsonmlir
docker image inspect jsonmlir

# Lancer les tests
docker run --rm jsonmlir

# Shell interactif
docker run --rm -it jsonmlir bash
python tests/run_tests.py --jobs 8

# Ou directement en passant les commandes
docker run --rm jsonmlir python tests/run_tests.py --jobs 8
docker run --rm jsonmlir python examples/python_max/main.py
docker run --rm jsonmlir python src/jsonmlir/pipeline/cli.py examples/somme/main.json -C  
```



## Installation manuelle

En cas de problème, vous pouvez aussi regarder le dockerfile.

```shell
# Environnement python
uv python install 3.13
uv venv ~/.venv/mlirdev --python 3.13
source ~/.venv/mlirdev/bin/activate
uv pip install --upgrade pip

# Cloner LLVM
LLVM_PROJECT_PATH=~/llvm-project
git clone --depth=1 https://github.com/llvm/llvm-project --branch llvmorg-22.1.8 $LLVM_PROJECT_PATH
uv pip install -r "$LLVM_PROJECT_PATH/mlir/python/requirements.txt"

# Build des bindings Python
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

# check-mlir-python : ~4 tests en échec sur ~100 ; vérifier manuellement si besoin
ninja -C "$LLVM_PROJECT_PATH/build" check-mlir-python || true

# Enregistrer le package MLIR dans le venv
MLIR_CORE="$LLVM_PROJECT_PATH/build/tools/mlir/python_packages/mlir_core"
echo "$MLIR_CORE" > "$VIRTUAL_ENV/lib/python3.13/site-packages/mlir_core.pth"
uv run python -c "import mlir.ir; print('OK')"

# Lancer les tests
uv run python tests/run_tests.py -j 8
```
