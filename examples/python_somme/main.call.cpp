#include "../memref_bridge.h"

#include <cstdint>
#include <cstdio>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(int64_t max);

void print_int(int64_t value) {
  std::printf("%ld\n", static_cast<long>(value));
}
}

int main() {
  const int64_t result = _mlir_ciface_lib_main(10);
  std::cout << "lib_main(10) = " << result << std::endl;
  std::cout << "EXPECT '45', got '" << result << "'" << std::endl;
  return 0;
}
