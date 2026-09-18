#include "../memref_bridge.h"

#include <cstddef>
#include <cstdint>
#include <iostream>

// MdSpan
//   [0..7]   data (ptr to memory buffer, 64 bits)
//   [8..11]  padding (32 bits)
//   [12..15] size (i32, number of elements)

extern "C" {
struct MdSpan {
  int64_t *data;
  int32_t padding;
  int32_t size;
};
int32_t _mlir_ciface_lib_main(uintptr_t span_ptr);
}

int main() {
  static_assert(sizeof(MdSpan) == 16);
  static_assert(offsetof(MdSpan, data) == 0);
  static_assert(offsetof(MdSpan, size) == 12);

  constexpr int32_t n_elements = 5;
  int64_t buffer[n_elements] = {10, 20, 30, 40, 50};
  int64_t expected[n_elements] = {11, 21, 31, 41, 51};

  MdSpan span = {buffer, 0, n_elements};

  const int32_t result =
      _mlir_ciface_lib_main(reinterpret_cast<uintptr_t>(&span));

  std::cout << "Edit through mdspan" << std::endl;
  std::cout << "EXPECTED size '" << n_elements << "', got '" << result << "'"
            << std::endl;
  for (int32_t i = 0; i < n_elements; i++) {
    std::cout << "EXPECTED buffer[" << i << "] '" << expected[i] << "', got '"
              << buffer[i] << "'" << std::endl;
  }
  return 0;
}
