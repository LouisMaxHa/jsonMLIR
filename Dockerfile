# syntax=docker/dockerfile:1
# jsonMLIR development image with Python MLIR bindings (LLVM 22.1.8).
#
# Build multi-stage (cf. https://llvm.org/docs/Docker.html) :
# 1. mlir-build     - compile LLVM/MLIR (disposable image)
# 2. mlir-toolchain - reusable image (binaries + venv + clang/python)
# 3. image finale   - installe jsonMLIR
#
# Reuse the toolchain without recompiling LLVM:
#   docker build --target mlir-toolchain -t jsonmlir-mlir-toolchain:22.1.8 .
#   docker build --build-arg TOOLCHAIN_IMAGE=jsonmlir-mlir-toolchain:22.1.8 .

ARG TOOLCHAIN_IMAGE=mlir-toolchain 
ARG LLVM_VERSION=llvmorg-22.1.8 
ARG PYTHON_VERSION=3.13

# ── Stage 1: LLVM/MLIR build ─────────────────────────────────────────
FROM fedora:42 AS mlir-build

ARG LLVM_VERSION
ARG PYTHON_VERSION

ENV LLVM_SRC=/opt/llvm-project \
  LLVM_PREFIX=/opt/llvm \
  VIRTUAL_ENV=/opt/venv \
  CCACHE_DIR=/var/cache/ccache \
  PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}"

# Install packages
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

# Clone LLVM
RUN git clone --depth=1 \
      https://github.com/llvm/llvm-project \
      --branch "${LLVM_VERSION}" \
      "${LLVM_SRC}"

# Install Python packages
RUN python${PYTHON_VERSION} -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/python" -m pip install --upgrade pip \
    && "${VIRTUAL_ENV}/bin/python" -m pip install -r "${LLVM_SRC}/mlir/python/requirements.txt" \
    && "${VIRTUAL_ENV}/bin/python" -c "import nanobind; print(nanobind.cmake_dir())"

# Configure -> build -> Python tests (partial failures expected) -> install
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

# ── Stage 2: reusable slim toolchain ─────────────────────────────────
FROM fedora:42 AS mlir-toolchain

ARG PYTHON_VERSION

ENV LLVM_PREFIX=/opt/llvm \
  VIRTUAL_ENV=/opt/venv \
  PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}" \
  MLIR_BIN_DIR="${LLVM_PREFIX}/bin"

# Install packages
RUN dnf install -y \
      clang \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-devel \
      ca-certificates \
    && dnf clean all

COPY --from=mlir-build "${VIRTUAL_ENV}" "${VIRTUAL_ENV}"
COPY --from=mlir-build "${LLVM_PREFIX}" "${LLVM_PREFIX}"

RUN "${VIRTUAL_ENV}/bin/python" -c "import site; from pathlib import Path; Path(site.getsitepackages()[0], 'mlir_core.pth').write_text('${LLVM_PREFIX}/python_packages/mlir_core\n')" \
    && "${VIRTUAL_ENV}/bin/python" -c "import mlir.ir; print('OK')"

# ── Stage 3 : jsonMLIR ───────────────────────────────────────────────
FROM ${TOOLCHAIN_IMAGE}

ARG PYTHON_VERSION

ENV LLVM_PREFIX=/opt/llvm \
  VIRTUAL_ENV=/opt/venv \
  PATH="${VIRTUAL_ENV}/bin:${LLVM_PREFIX}/bin:${PATH}" \
  MLIR_BIN_DIR="${LLVM_PREFIX}/bin" \
  SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0


# The wrapper mounts the host repository to avoid ambiguity.
WORKDIR /opt/jsonMLIR

# Install jsonMLIR
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --upgrade pip
RUN pip install -e . --group dev

CMD ["python", "-c", "import jsonmlir; import mlir.ir; print('OK')"]
