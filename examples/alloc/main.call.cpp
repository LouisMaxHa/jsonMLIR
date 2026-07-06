#include <cstdint>
#include <iostream>

extern "C" {
  int64_t *_mlir_ciface_xdsl_main(uint64_t size);
}

int main() {

  uint64_t size = 5;
  int64_t expected[5] = {0, 1, 2, 3, 4};

  int64_t *myArray = _mlir_ciface_xdsl_main(size);

  // TESTS
  for (int i = 0; i < size; i++) {
    std::cout << "EXPECTED '" << expected[i] << "', got '" << myArray[i]
              << "'" << std::endl;
  }
  return 0;
}
