#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(int64_t x, int64_t y);
}

int main() {
  // _mlir_ciface_lib_main(x, y) = -x + !y
  // x = 7, y = 0 -> -7
  const int64_t r1 = _mlir_ciface_lib_main(7, 0);
  std::cout << "lib_main(7, 0) = " << r1 << std::endl;
  std::cout << "EXPECT '-6', got '" << r1 << "'" << std::endl;

  // x = 3, y = !1 = 0 -> 3 + 0
  const int64_t r2 = _mlir_ciface_lib_main(-3, 1);
  std::cout << "lib_main(-3, 1) = " << r2 << std::endl;
  std::cout << "EXPECT '3', got '" << r2 << "'" << std::endl;

  // x = -10, y = !4 = 5 -> 10 + 5
  const int64_t r3 = _mlir_ciface_lib_main(-10, 4);
  std::cout << "lib_main(-10, 4) = " << r3 << std::endl;
  std::cout << "EXPECT '15', got '" << r3 << "'" << std::endl;

  return 0;
}
