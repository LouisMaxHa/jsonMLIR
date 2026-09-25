#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>

// The byte layout must match DefineStruct("Real2", 16, ...):
//   [0..7]   x
//   [8..15]  y
struct Real2 {
  double x;
  double y;
};

struct Real2Mdspan {
  Real2 *data;
  int32_t cell_count;
  int32_t nodes_per_cell;
};

static_assert(sizeof(Real2) == 16);
static_assert(offsetof(Real2, x) == 0);
static_assert(offsetof(Real2, y) == 8);
static_assert(sizeof(Real2Mdspan) == 16);
static_assert(offsetof(Real2Mdspan, data) == 0);
static_assert(offsetof(Real2Mdspan, cell_count) == 8);
static_assert(offsetof(Real2Mdspan, nodes_per_cell) == 12);

extern "C" {
void _mlir_ciface_lib_main(uintptr_t coordinates, int64_t cell, int64_t node);
}

int main() {
  constexpr int32_t cell_count = 2;
  constexpr int32_t nodes_per_cell = 4;
  constexpr int32_t selected_cell = 1;
  constexpr int32_t selected_node = 2;

  Real2 coordinates[2][4] = {
      {{0.0, 0.0}, {1.0, 0.0}, {2.0, 0.0}, {3.0, 0.0}}, // {x, y}
      {{0.0, 1.0}, {1.0, 1.0}, {2.0, 1.0}, {3.0, 1.0}},
  };

  Real2Mdspan view{
      &coordinates[0][0],
      cell_count,
      nodes_per_cell,
  };
  Real2 &selected = coordinates[selected_cell][selected_node];
  const double old_y = selected.y;
  _mlir_ciface_lib_main(reinterpret_cast<uintptr_t>(&view), selected_cell,
                        selected_node);

  std::cout << "Coordinate [1][2].x EXPECTED '10' got '" << selected.x << "'"
            << std::endl;
  std::cout << "Coordinate [1][2].y EXPECTED '11' got '" << selected.y << "'"
            << std::endl;
  return 0;
}
