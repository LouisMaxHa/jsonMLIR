# Installation

Deux options : installation manuelle, ou image Docker (recommandée pour éviter de polluer la machine hôte).

Doc MLIR : [`mlir/docs/Bindings/Python.md`](https://mlir.llvm.org/docs/Bindings/Python/).

## Option A — Docker

Un [`Dockerfile`](./Dockerfile) à la racine du dépôt construit LLVM/MLIR (tag `llvmorg-22.1.8`), les bindings Python, puis installe jsonMLIR.

```shell
# Depuis la racine du dépôt (build long : 1–2 h, plusieurs Go)
docker build -t jsonmlir .

# Vérifier les bindings MLIR
docker run --rm jsonmlir python -c "import mlir.ir; print('OK')"

# Lancer les tests (commande par défaut de l'image)
docker run --rm jsonmlir

# Shell interactif
docker run --rm -it jsonmlir bash
```

Pour monter le dépôt en volume (édition locale, exécution dans le conteneur) :

```shell
docker run --rm -it -v "$PWD:/opt/jsonMLIR" -w /opt/jsonMLIR jsonmlir bash
```

## Option B — Installation manuelle

### Environnement Python

```shell
uv python install 3.13
uv venv ~/.venv/mlirdev --python 3.13
source ~/.venv/mlirdev/bin/activate
uv pip install --upgrade pip
```

### Clone LLVM

```shell
LLVM_PROJECT_PATH=~/llvm-project
git clone --depth=1 https://github.com/llvm/llvm-project --branch llvmorg-22.1.8 $LLVM_PROJECT_PATH
uv pip install -r "$LLVM_PROJECT_PATH/mlir/python/requirements.txt"
```

### Build des bindings Python

```shell
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
```

### Enregistrer le package MLIR dans le venv

```shell
MLIR_CORE="$LLVM_PROJECT_PATH/build/tools/mlir/python_packages/mlir_core"
echo "$MLIR_CORE" > "$VIRTUAL_ENV/lib/python3.13/site-packages/mlir_core.pth"

uv run python -c "import mlir.ir; print('OK')"
```

### Installer jsonMLIR

```shell
git clone git@github.com:LouisMaxHa/jsonMLIR.git
cd jsonMLIR
uv sync
uv run python tests/run_tests.py -j 8
```
