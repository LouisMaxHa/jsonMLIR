# syntax=docker/dockerfile:1
# Image de développement jsonMLIR + bindings Python MLIR (LLVM 22.1.8).
# La compilation de LLVM peut prendre 1–2 h et plusieurs Go d'espace disque.

FROM fedora:42

ARG LLVM_VERSION=llvmorg-22.1.8
ARG PYTHON_VERSION=3.13
ENV LLVM_PROJECT_PATH=/opt/llvm-project
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${LLVM_PROJECT_PATH}/build/bin:${PATH}"
ENV PYTHONPATH=""

RUN dnf install -y \
      clang \
      cmake \
      ccache \
      git \
      lld \
      ninja-build \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-devel \
      curl \
      ca-certificates \
    && dnf clean all

# uv (gestionnaire Python)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN uv venv "${VIRTUAL_ENV}" --python "${PYTHON_VERSION}" \
    && uv pip install --python "${VIRTUAL_ENV}/bin/python" --upgrade pip

# Clone et build LLVM/MLIR + bindings Python
RUN git clone --depth=1 \
      https://github.com/llvm/llvm-project \
      --branch "${LLVM_VERSION}" \
      "${LLVM_PROJECT_PATH}" \
    && uv pip install --python "${VIRTUAL_ENV}/bin/python" \
         -r "${LLVM_PROJECT_PATH}/mlir/python/requirements.txt" \
    && cmake -G Ninja \
      -S "${LLVM_PROJECT_PATH}/llvm" \
      -B "${LLVM_PROJECT_PATH}/build" \
      -DLLVM_ENABLE_PROJECTS=mlir \
      -DLLVM_BUILD_EXAMPLES=ON \
      -DLLVM_TARGETS_TO_BUILD="Native;NVPTX;AMDGPU" \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLVM_ENABLE_ASSERTIONS=ON \
      -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
      -DPython3_EXECUTABLE="${VIRTUAL_ENV}/bin/python" \
      -DPython_EXECUTABLE="${VIRTUAL_ENV}/bin/python" \
      -DCMAKE_C_COMPILER=clang \
      -DCMAKE_CXX_COMPILER=clang++ \
      -DLLVM_ENABLE_LLD=ON \
    && cmake --build "${LLVM_PROJECT_PATH}/build" \
    && ninja -C "${LLVM_PROJECT_PATH}/build" check-mlir-python || true

# Exposer mlir_core au venv
RUN MLIR_CORE="${LLVM_PROJECT_PATH}/build/tools/mlir/python_packages/mlir_core" \
    && echo "${MLIR_CORE}" > "${VIRTUAL_ENV}/lib/python${PYTHON_VERSION}/site-packages/mlir_core.pth" \
    && python -c "import mlir.ir; print('OK')"

WORKDIR /opt/jsonMLIR
COPY . /opt/jsonMLIR

# hatch-vcs : pas de .git dans le contexte Docker
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
RUN uv sync

CMD ["uv", "run", "python", "tests/run_tests.py", "-j", "8"]
