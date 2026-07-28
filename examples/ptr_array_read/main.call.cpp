#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(uintptr_t data_ptr, int64_t idx);
}

int main() {
  int64_t myData[5] = {10, 11, 12, 13, 14};
  int64_t expected[5] = {10, 11, 12, 13, 14};
  uintptr_t data_ptr = (uintptr_t)myData;

  for (int i = 0; i < 5; i++) {
    const int64_t result = _mlir_ciface_lib_main(data_ptr, (int64_t)i);
    std::cout << "Indice : " << i << " EXPECTED '" << expected[i] << "', got '"
              << result << "'" << std::endl;
  }
  return 0;
}
