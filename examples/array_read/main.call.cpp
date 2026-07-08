#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_xdsl_main(MemRefType<int64_t, 1>* array, int index);
}

int main() {
  int64_t myData[5] = {10, 11, 12, 13, 14};
  MemRefType<int64_t, 1> myMemref = make_memref_1d<int64_t>(myData, 5, 1);

  for (int i = 0; i < 5; i++) {
    const int64_t result = _mlir_ciface_xdsl_main(&myMemref, i);
    std::cout << "EXPECTED '" << myData[i] << "', got '" << result << "'"
              << std::endl;
  }
  return 0;
}
