# syntax=docker/dockerfile:1
# Image de développement jsonMLIR + bindings Python MLIR (LLVM 22.1.8).
#
# Build multi-stage (cf. https://llvm.org/docs/Docker.html) :
# 1. mlir-build     - compile LLVM/MLIR (image jetable)
# 2. mlir-toolchain - image réutilisable (binaires + venv + clang/python)
# 3. image finale   - installe jsonMLIR
#
# Réutiliser la toolchain sans recompiler LLVM :
#   docker build --target mlir-toolchain -t jsonmlir-mlir-toolchain:22.1.8 .
#   docker build --build-arg TOOLCHAIN_IMAGE=jsonmlir-mlir-toolchain:22.1.8 .

ARG TOOLCHAIN_IMAGE=mlir-toolchain
ARG LLVM_VERSION=llvmorg-22.1.8
ARG PYTHON_VERSION=3.13

# ── Stage 1 : compilation LLVM/MLIR ──────────────────────────────────
FROM fedora:42 AS mlir-build

ARG LLVM_VERSION
ARG PYTHON_VERSION

ENV LLVM_SRC=/opt/llvm-project
ENV LLVM_PREFIX=/opt/llvm
ENV VIRTUAL_ENV=/opt/venv
ENV CCACHE_DIR=/var/cache/ccache
ENV PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}"

# Installation des packages
RUN dnf install -y \
      clang \
      cmake \
      ccache \
      git \
      lld \
      ninja-build \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-devel \
      ca-certificates \
    && dnf clean all \
    && ccache --set-config=max_size=10G

# Clone de LLVM
RUN git clone --depth=1 \
      https://github.com/llvm/llvm-project \
      --branch "${LLVM_VERSION}" \
      "${LLVM_SRC}"

# Installation des packages pythons
RUN python${PYTHON_VERSION} -m venv "${VIRTUAL_ENV}" \
    && pip install --upgrade pip \
    && pip install -r "${LLVM_SRC}/mlir/python/requirements.txt"

# Configure -> build -> tests Python (échecs partiels attendus) -> install
RUN cmake -G Ninja \
      -S "${LLVM_SRC}/llvm" \
      -B "${LLVM_SRC}/build" \
      -DCMAKE_INSTALL_PREFIX="${LLVM_PREFIX}" \
      -DLLVM_ENABLE_PROJECTS=mlir \
      -DLLVM_TARGETS_TO_BUILD=Native \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLVM_ENABLE_ASSERTIONS=ON \
      -DLLVM_BUILD_EXAMPLES=OFF \
      -DLLVM_BUILD_TESTS=OFF \
      -DLLVM_INCLUDE_TESTS=OFF \
      -DLLVM_INCLUDE_EXAMPLES=OFF \
      -DMLIR_INCLUDE_TESTS=ON \
      -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
      -DPython3_EXECUTABLE="${VIRTUAL_ENV}/bin/python" \
      -DPython_EXECUTABLE="${VIRTUAL_ENV}/bin/python" \
      -DCMAKE_C_COMPILER=clang \
      -DCMAKE_CXX_COMPILER=clang++ \
      -DLLVM_ENABLE_LLD=ON \
      -DLLVM_CCACHE_BUILD=ON \
    && ninja -C "${LLVM_SRC}/build" \
         mlir-opt \
         mlir-translate \
         llc \
         opt \
         MLIRPythonModules \
    && (ninja -C "${LLVM_SRC}/build" check-mlir-python || true) \
    && ninja -C "${LLVM_SRC}/build" \
         install-mlir-opt \
         install-mlir-translate \
         install-llc \
         install-opt \
         install-MLIRPythonModules \
    && ccache -s

# ── Stage 2 : toolchain slim réutilisable ────────────────────────────
FROM fedora:42 AS mlir-toolchain

ARG PYTHON_VERSION

ENV LLVM_PREFIX=/opt/llvm
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}"
ENV MLIR_BIN_DIR="${LLVM_PREFIX}/bin"

# Installation des packages
RUN dnf install -y \
      clang \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-devel \
      ca-certificates \
    && dnf clean all

COPY --from=mlir-build "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=mlir-build "${LLVM_PREFIX}" "${LLVM_PREFIX}"

RUN echo "${LLVM_PREFIX}/python_packages/mlir_core" \
      > "${VIRTUAL_ENV}/lib/python${PYTHON_VERSION}/site-packages/mlir_core.pth" \
    && python -c "import mlir.ir; print('OK')"

# ── Stage 3 : jsonMLIR ───────────────────────────────────────────────
FROM ${TOOLCHAIN_IMAGE}

ARG PYTHON_VERSION

ENV LLVM_PREFIX=/opt/llvm
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}"
ENV MLIR_BIN_DIR="${LLVM_PREFIX}/bin"

# hatch-vcs : pas de .git dans le contexte Docker (.dockerignore)
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0

WORKDIR /opt/jsonMLIR
COPY . /opt/jsonMLIR

# Installation de jsonMLIR
RUN pip install --upgrade pip \
    && pip install -e . --group dev

CMD ["python", "tests/run_tests.py", "-j", "8"]
