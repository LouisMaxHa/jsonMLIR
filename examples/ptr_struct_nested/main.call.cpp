#include "../memref_bridge.h"

#include <cstddef>
#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(uintptr_t data_ptr, size_t i);
}

struct xyz {
  int64_t x;
  int64_t y;
  int64_t z;
};

struct Noeuds {
  xyz *coords;
  int64_t size;
};

struct Simulation {
  Noeuds *positions;
  Noeuds *temperatures;
};

int ctr = 0;
int get_value() { return ctr++; }

int main() {

  // ──────────── Tableaux contenant les informations ────────────
  xyz *coords_positions = new xyz[5];
  for (int i = 0; i < 5; i++) {
    coords_positions[i].x = get_value();
    coords_positions[i].y = get_value();
    coords_positions[i].z = get_value();
  }

  xyz *coords_temperatures = new xyz[5];
  for (int i = 0; i < 5; i++) {
    coords_temperatures[i].x = get_value();
    coords_temperatures[i].y = get_value();
    coords_temperatures[i].z = get_value();
  }

  // ──────────── Description des tableaux ────────────
  Noeuds *noeuds_positions = new Noeuds;
  noeuds_positions->coords = coords_positions;
  noeuds_positions->size = 5;

  Noeuds *noeuds_temperatures = new Noeuds;
  noeuds_temperatures->coords = coords_temperatures;
  noeuds_temperatures->size = 5;

  // ──────────── Simulation ────────────
  Simulation *simu = new Simulation;
  simu->positions = noeuds_positions;
  simu->temperatures = noeuds_temperatures;

  uintptr_t simu_ptr = (uintptr_t)simu;

  std::cout << "Offset temperatures : " << offsetof(Simulation, temperatures)
            << std::endl;

  for (int i = 0; i < 5; i++) {
    const int64_t result = _mlir_ciface_lib_main(simu_ptr, i);
    std::cout << " EXPECTED '" << simu->temperatures->coords[i].y << "', got '"
              << result << "'" << std::endl;
  }
}
