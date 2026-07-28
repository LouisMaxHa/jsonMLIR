#include "../memref_bridge.h"

#include <cstdint>
#include <iostream>

extern "C" {
int64_t _mlir_ciface_lib_main(MemRefType<int64_t, 2> *matrix);
}

int main() {
  int64_t matrix[5][5] = {{0, 0, 0, 0, 0},
                          {0, 1, 0, 0, 0},
                          {0, 0, 2, 0, 0},
                          {0, 0, 0, 3, 0},
                          {0, 0, 0, 0, 4}};

  /*
  template <typename T, int Rank> struct MemRefType {
      T *basePtr;
      T *data;
      int64_t offset;
      int64_t sizes[Rank];
      int64_t strides[Rank];
  };*/

  MemRefType<int64_t, 2> myMemref = {
      &matrix[0][0], &matrix[0][0], 0, {5, 5}, {5, 1}};

  const int64_t result = _mlir_ciface_lib_main(&myMemref);
  std::cout << "EXPECTED '10', got '" << result << "'" << std::endl;
  return 0;
}
