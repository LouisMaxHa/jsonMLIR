#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
void _mlir_ciface_lib_main(uintptr_t data_ptr, uint64_t size);
}

int main() {
  int64_t myDataBase[5] = {10, 11, 12, 13, 14};
  int64_t myData[5] = {10, 11, 12, 13, 14};
  uint64_t size = 5;
  uintptr_t data_ptr = (uintptr_t)myData;

  std::cout << "Array before:" << std::endl;
  for (auto i : myData) {
    std::cout << i << " ";
  }
  std::cout << std::endl;

  _mlir_ciface_lib_main(data_ptr, size);

  std::cout << "Array after:" << std::endl;
  for (auto i : myData) {
    std::cout << i << " ";
  }
  std::cout << std::endl;

  // TESTS
  for (int i = 0; i < 5; i++) {
    std::cout << "EXPECTED '" << myDataBase[i] + 1 << "', got '" << myData[i]
              << "'" << std::endl;
  }
  return 0;
}
