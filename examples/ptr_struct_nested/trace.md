```cpp
struct xyz {
  int64_t x;
  int64_t y;
  int64_t z;
};

struct Noeuds {
  xyz* coords;
  int64_t size;
};

struct Simulation {
  Noeuds* positions;
  Noeuds* temperatures;
};
```
```json
{ "op": "var", "name": "simuReference",
  "indices": ["*", "positions", "*", "coords", "*", 3, "z"]
}
```

```cpp
define i64 @_mlir_ciface_lib_main(i64 %0, i64 %1) local_unnamed_addr #0 {
  %3 = inttoptr i64 %0 to ptr     // ptr simu 
  %4 = load i64, ptr %3, align 4  // i64 noeuds
  %5 = inttoptr i64 %4 to ptr     // ptr noeuds
  %6 = load i64, ptr %5, align 4  // i64 xyz ????
  %7 = add i64 %6, 11             // On ajoute 11 ? Pourquoi pas 24 ? Ou même 3*24 ? 
                                  // 11: (x, y, z), (x, y, z), (x, y, z), (x, y, z)
                                  //      0  1  2    3  4  5    6  7  8    9 10 11
                                  // N'a pas l'air de changer :/
  %8 = inttoptr i64 %7 to ptr     // ptr xyz
  %9 = load i64, ptr %8, align 4  // y
  ret i64 %9
}
```