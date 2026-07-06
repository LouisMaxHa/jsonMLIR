#include "../memref_bridge.h"

#include <cassert>
#include <cstddef>
#include <cstdint>
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
double _mlir_ciface_xdsl_main(MemRefType<int8_t, 1> *bytes);
}

int main() {
  constexpr int64_t node_count = 1;
  constexpr int64_t node_size = 16;
  constexpr int64_t struct_size = node_size * node_count;

  Noeud noeud = {2, 0.3};
  std::cout << offsetof(Noeud, capacite) << " " << offsetof(Noeud, temperature)
            << " " << sizeof(Noeud) << std::endl;

  assert(sizeof(Noeud) == node_size);
  assert(offsetof(Noeud, capacite) == 0);
  assert(offsetof(Noeud, temperature) == 8);

  MemRefType<int8_t, 1> bytes =
      make_memref_1d<int8_t>(reinterpret_cast<int8_t *>(&noeud), struct_size);

  const double result = _mlir_ciface_xdsl_main(&bytes);
  std::cout << "Edit struct" << std::endl;
  std::cout << "EXPECTED read temperature '0.3', got '" << result << "'"
            << std::endl;
  return 0;
}
