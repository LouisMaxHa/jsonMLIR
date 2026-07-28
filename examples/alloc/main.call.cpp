#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
MemRefType<int64_t, 1> _mlir_ciface_lib_main(uint64_t size);
}

int main() {

  uint64_t size = 5;
  int64_t expected[5] = {0, 1, 2, 3, 4};

  MemRefType<int64_t, 1> descriptor = _mlir_ciface_lib_main(size);
  int64_t *myArray = make_array(descriptor);

  // TESTS
  for (int i = 0; i < size; i++) {
    std::cout << "EXPECTED '" << expected[i] << "', got '" << myArray[i] << "'"
              << std::endl;
  }
  return 0;
}
