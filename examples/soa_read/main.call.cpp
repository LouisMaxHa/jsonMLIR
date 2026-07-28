#include "../memref_bridge.h"

#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>

// Noeud
//   [0..3]   capacite (i32)
//   [4..7]   padding
//   [8..15]  temperature (f64)
//   [16..23] padding

extern "C" {
struct Noeud {
  int capacite;
  double temperature;
};
double _mlir_ciface_lib_main(MemRefType<int8_t, 1> *bytes, int i);
}

int main() {
  constexpr int64_t node_count = 2;
  constexpr int64_t node_size = 16;
  constexpr int64_t buffer_size = node_size * node_count;

  std::cout << offsetof(Noeud, capacite) << " " << offsetof(Noeud, temperature)
            << " " << sizeof(Noeud) << std::endl;

  assert(sizeof(Noeud) == node_size);
  assert(offsetof(Noeud, capacite) == 0);
  assert(offsetof(Noeud, temperature) == 8);

  Noeud buffer[2] = {{1, 2.0}, {3, 4.0}};

  MemRefType<int8_t, 1> bytes =
      make_memref_1d<int8_t>(reinterpret_cast<int8_t *>(buffer), buffer_size);

  const double result0 = _mlir_ciface_lib_main(&bytes, 0);
  std::cout << "SoA read array[0].temperature, EXPECTED '2' = '" << result0
            << "'" << std::endl;
  const double result1 = _mlir_ciface_lib_main(&bytes, 1);
  std::cout << "SoA read array[1].temperature, EXPECTED '4' = '" << result1
            << "'" << std::endl;
  return 0;
}
