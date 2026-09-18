#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

// Un opérateur de structure est résolu via struct_method.py : Real3 + Real3
// applique `+f` champ par champ, puis renvoie une nouvelle Real3 (memref).
struct Real3 {
  double x;
  double y;
  double z;
};

extern "C" {
void _mlir_ciface_lib_main(MemRefType<int8_t, 1> *result,
                           MemRefType<int8_t, 1> *v1,
                           MemRefType<int8_t, 1> *v2);
}

int main() {
  constexpr int64_t struct_size = 24;

  Real3 v1 = {1.0, 2.0, 3.0};
  Real3 v2 = {0.5, 1.5, 2.5};

  MemRefType<int8_t, 1> d1 =
      make_memref_1d<int8_t>(reinterpret_cast<int8_t *>(&v1), struct_size);
  MemRefType<int8_t, 1> d2 =
      make_memref_1d<int8_t>(reinterpret_cast<int8_t *>(&v2), struct_size);
  MemRefType<int8_t, 1> result;

  _mlir_ciface_lib_main(&result, &d1, &d2);
  Real3 *v3 = reinterpret_cast<Real3 *>(make_array(result));

  std::cout << "Real3 + Real3" << std::endl;
  std::cout << "EXPECT '1.5' got '" << v3->x << "'" << std::endl;
  std::cout << "EXPECT '3.5' got '" << v3->y << "'" << std::endl;
  std::cout << "EXPECT '5.5' got '" << v3->z << "'" << std::endl;

  return 0;
}
