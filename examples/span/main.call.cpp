#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>

// std::span layout
//   [0..7]   data (ptr to memory buffer, 64 bits)
//   [8..15]  size (i64, number of elements)

extern "C" {
  int64_t _mlir_ciface_lib_main(uintptr_t span_ptr);
}

int main() {
  constexpr int32_t n_elements = 3;
  int64_t buffer[n_elements] = {10, 20, 30};
  int64_t expected[n_elements] = {11, 21, 31};

  std::span<int64_t> mySpan = {buffer, n_elements};

  const int64_t result =
      _mlir_ciface_lib_main(reinterpret_cast<uintptr_t>(&mySpan));

  std::cout << "Edit through span" << std::endl;
  std::cout << "EXPECTED size '" << n_elements << "', got '" << result << "'"
            << std::endl;
  for (int32_t i = 0; i < n_elements; i++) {
    std::cout << "EXPECTED buffer[" << i << "] '" << expected[i] << "', got '"
              << buffer[i] << "'" << std::endl;
  }
  return 0;
}
