#pragma once

#include <cstdint>

// Struct for memref, should match:
// {
//      T* allocated;         // start of the allocated storage
//      T* aligned;           // pointer to the first element
//      int64_t offset;       // shift of first element
//      
//      // number of elements along each dimension
//      int64_t size[Rank];
//      
//      // step between consecutive indices along each dimension,
//      // for example, if you want one element out of 2,
//      int64_t stride[Rank]; 
// }

template <typename T, int Rank> struct MemRefType {
  T *basePtr;
  T *data;
  int64_t offset;
  int64_t sizes[Rank];
  int64_t strides[Rank];
};

// Construit un descripteur zero-copy autour d'un buffer existant.
// `n` et `stride_in_elements` sont exprimés en unités de T (pas en octets).
template <typename T>
MemRefType<T, 1> make_memref_1d(
    T *data, int64_t n,
    int64_t stride_in_elements = 1
){
  return MemRefType<T, 1>{
    data /* Allocated */,
    data /* Aligned */,
    0    /* Offset */,
    {n}  /* Size */,
    {stride_in_elements} /* stride */,
  };
}

template <typename T>
T* make_array(MemRefType<T, 1> descriptor){
  return descriptor.basePtr;
}
