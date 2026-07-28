#include <cassert>
#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(uintptr_t addr);
}

int main() {
  int *addr = (int *)malloc(sizeof(int));
  (*addr) = 4;

  uintptr_t addr_ptr = (uintptr_t)addr;

  int64_t result = _mlir_ciface_lib_main(addr_ptr);
  std::cout << "Read int*" << std::endl;
  std::cout << "EXPECTED '4', got '" << result << "'" << std::endl;
  return 0;
}
