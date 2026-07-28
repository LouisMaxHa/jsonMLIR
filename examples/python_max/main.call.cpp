#include "../memref_bridge.h"

#include <cstdint>
#include <cstdio>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(int64_t x, int64_t y);

void print_int(int64_t value) {
  std::printf("%ld\n", static_cast<long>(value));
}
}

int main() {
  const int64_t r1 = _mlir_ciface_lib_main(3, 7);
  std::cout << "lib_main(3, 7) = " << r1 << std::endl;
  std::cout << "EXPECT '7', got '" << r1 << "'" << std::endl;

  const int64_t r2 = _mlir_ciface_lib_main(10, 4);
  std::cout << "lib_main(10, 4) = " << r2 << std::endl;
  std::cout << "EXPECT '10', got '" << r2 << "'" << std::endl;

  return 0;
}
