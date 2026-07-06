#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_xdsl_main(MemRefType<int64_t, 1> *array, int size);
}

int main() {
  int64_t myData[5] = {10, 11, 12, 13, 14};
  int64_t expected[5] = {11, 12, 13, 14, 15};
  size_t size = 5;
  MemRefType<int64_t, 1> myMemref = make_memref_1d<int64_t>(myData, 5, 1);

  std::cout << "Array before:" << std::endl;
  for (auto i : myData) {
    std::cout << i << " ";
  }
  std::cout << std::endl;

  const int64_t result = _mlir_ciface_xdsl_main(&myMemref, size);

  std::cout << "Array after:" << std::endl;
  for (auto i : myData) {
    std::cout << i << " ";
  }
  std::cout << std::endl;

  // TESTS
  for (int i = 0; i < 5; i++) {
    std::cout << "EXPECTED '" << expected[i] << "', got '" << myData[i] << "'"
              << std::endl;
  }

  std::cout << "Reading array : xdsl_main(myMemref) = " << result << '\n';
  return 0;
}
