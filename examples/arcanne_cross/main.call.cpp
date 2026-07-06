#include "../memref_bridge.h"

#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>

// Noeud
//   [0..3]   capacite (i32)
//   [4..7]   padding
//   [8..15]  temperature (f64)
//   [16..23] padding

struct Real3 {
  float_t x;
  float_t y;
  float_t z;
};


Real3 cross(Real3 v1, Real3 v2) {
  Real3 v;
  v.x = v1.y * v2.z - v1.z * v2.y;
  v.y = v2.x * v1.z - v2.z * v1.x;
  v.z = v1.x * v2.y - v1.y * v2.x;
  return v;
}

extern "C" {
  MemRefType<u_int8_t, 1> _mlir_ciface_xdsl_main(Real3* v1, Real3* v2);
}


int main() {

  Real3 v1 = {0.1, 0.2, 0.3};
  Real3 v2 = {0.4, 0.5, 0.6};
  Real3 expected = cross(v1, v2);
  
  MemRefType<u_int8_t, 1> descriptor = _mlir_ciface_xdsl_main(&v1, &v2);
  Real3* v3 = (Real3*)make_array(descriptor);

  std::cout << "EXPECTED '" << expected.x << "' got '" << v3->x << "'" << std::endl;
  std::cout << "EXPECTED '" << expected.y << "' got '" << v3->y << "'" << std::endl;
  std::cout << "EXPECTED '" << expected.z << "' got '" << v3->z << "'" << std::endl;
  return 0;
}
