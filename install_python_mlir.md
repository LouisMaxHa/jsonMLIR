# Utiliser les bindings Python de MLIR

```shell
# Installer un CPython 3.13 géré par uv (si besoin)
uv python install 3.13

# Si .venv existe déjà (créé par `uv sync`, Python 3.13 épinglé dans
# .python-version), sauter le `uv venv` et juste activer.
uv venv .venv --python 3.13
source .venv/bin/activate
uv pip install --upgrade pip


# Chemin vers llvm-project. Ne PAS `cd` dedans : il contient son propre
# pyproject.toml, donc `uv` y découvrirait un autre projet et utiliserait
# un autre venv que celui de xdsl-json.
LLVM_PROJECT_PATH=~/git/llvm22.1.8
uv pip install -r "$LLVM_PROJECT_PATH/mlir/python/requirements.txt"

# Pas besoin de `uv run` : cmake/ninja ne sont pas des outils Python,
# le venv activé + Python3_EXECUTABLE suffisent.
cmake -G Ninja -S "$LLVM_PROJECT_PATH/llvm" -B "$LLVM_PROJECT_PATH/build" \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
  -DPython3_EXECUTABLE="$VIRTUAL_ENV/bin/python" \
  -DPython_EXECUTABLE="$VIRTUAL_ENV/bin/python" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$LLVM_PROJECT_PATH/build"
ninja -C "$LLVM_PROJECT_PATH/build" check-mlir-python


# Exposer les bindings dans le venv via un .pth (chemin absolu car ~ est
# développé à l'affectation de LLVM_PROJECT_PATH).
MLIR_CORE="$LLVM_PROJECT_PATH/build/tools/mlir/python_packages/mlir_core"
echo "$MLIR_CORE" > "$VIRTUAL_ENV/lib/python3.13/site-packages/mlir_core.pth"
python -c "import mlir.ir; print('OK')"
```

Note : un `uv sync` ultérieur retirera du venv les dépendances du build
(numpy, nanobind, pybind11…) car elles ne sont pas dans `pyproject.toml`.
Sans conséquence pour utiliser les bindings ; les réinstaller (commande
`uv pip install -r …` ci-dessus) seulement pour relancer le build ou ses tests.

Doc : `mlir/docs/Bindings/Python.md`.
