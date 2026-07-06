#include "../memref_bridge.h"

#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <sys/types.h>

extern "C" {
  MemRefType<u_int8_t, 1> _mlir_ciface_xdsl_main();
}
struct Real3 {
  double_t x;
  double_t y;
  double_t z;
};

int main() {
  Real3 expected = {0.1, 0.2, 0.3};

  MemRefType<u_int8_t, 1> descriptor = _mlir_ciface_xdsl_main();
  Real3 *mystruct = (Real3 *)make_array(descriptor);

  std::cout << "offsetof(Real3, x) : " << offsetof(Real3, x) << std::endl;
  assert(offsetof(Real3, x) == 0);
  std::cout << "offsetof(Real3, y) : " << offsetof(Real3, y) << std::endl;
  assert(offsetof(Real3, y) == 8);
  std::cout << "offsetof(Real3, z) : " << offsetof(Real3, z) << std::endl;
  assert(offsetof(Real3, z) == 16);

  // TESTS
  std::cout << "x EXPECTED '" << expected.x << "', got '" << mystruct->x << "'" << std::endl;
  std::cout << "y EXPECTED '" << expected.y << "', got '" << mystruct->y << "'" << std::endl;
  std::cout << "z EXPECTED '" << expected.z << "', got '" << mystruct->z << "'" << std::endl;
  return 0;
}
