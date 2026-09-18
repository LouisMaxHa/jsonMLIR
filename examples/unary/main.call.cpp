#include <cstdint>
#include <iostream>

// Unary operators described by examples/unary/main.py :
//   -f x  ->  x *f -1.0
//   -  x  ->  x  * -1
//   !x    ->  x xor true
extern "C" {
  double _mlir_ciface_test_neg_float(double x);
  int64_t _mlir_ciface_test_neg_int(int64_t x);
  bool _mlir_ciface_test_neg_bool(bool x);
}

static void check_neg_float(double x) {
  const double expected = -x;
  const double got = _mlir_ciface_test_neg_float(x);
  std::cout << "test_neg_float(" << x << ") = " << got << std::endl;
  std::cout << "EXPECT '" << expected << "' got '" << got << "'" << std::endl;
}

static void check_neg_int(int64_t x) {
  const int64_t expected = -x;
  const int64_t got = _mlir_ciface_test_neg_int(x);
  std::cout << "test_neg_int(" << x << ") = " << got << std::endl;
  std::cout << "EXPECT '" << expected << "' got '" << got << "'" << std::endl;
}

static void check_neg_bool(bool x) {
  const bool expected = !x;
  const bool got = _mlir_ciface_test_neg_bool(x);
  std::cout << "test_neg_bool(" << x << ") = " << got << std::endl;
  std::cout << "EXPECT '" << expected << "' got '" << got << "'" << std::endl;
}

int main() {
  check_neg_float(3.5);
  check_neg_float(-2.0);

  check_neg_int(7);
  check_neg_int(-42);

  check_neg_bool(true);
  check_neg_bool(false);

  return 0;
}
