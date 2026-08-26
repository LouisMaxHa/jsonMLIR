from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from functools import partial

from mlir.ir import (
    F16Type,
    F32Type,
    F64Type,
    IndexType,
    IntegerType,
    Type,
)


class ScalarFamily(StrEnum):
    int = "int"
    float = "float"
    idx = "index"


def _int_type(width: int) -> Callable[[], Type]:
    return partial(IntegerType.get_signless, width)


class Scalar(StrEnum):
    """Scalaire MLIR. La valeur JSON est le nom (``i64``, ``index``, …)."""

    _family: ScalarFamily
    _byte_size: int
    _make_type: Callable[[], Type] | None

    def __new__(
        cls,
        value: str,
        family: ScalarFamily,
        byte_size: int,
        make_type: Callable[[], Type] | None = None,
    ):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._family = family
        obj._byte_size = byte_size
        obj._make_type = make_type
        return obj

    i64 = "i64", ScalarFamily.int, 8, _int_type(64)
    i32 = "i32", ScalarFamily.int, 4, _int_type(32)
    i16 = "i16", ScalarFamily.int, 2, _int_type(16)
    i8 = "i8", ScalarFamily.int, 1, _int_type(8)
    i1 = "i1", ScalarFamily.int, 1, _int_type(1)
    I64 = "I64", ScalarFamily.int, 8, _int_type(64)
    I32 = "I32", ScalarFamily.int, 4, _int_type(32)
    I16 = "I16", ScalarFamily.int, 2, _int_type(16)
    I8 = "I8", ScalarFamily.int, 1, _int_type(8)
    I1 = "I1", ScalarFamily.int, 1, _int_type(1)
    f16 = "f16", ScalarFamily.float, 2, F16Type.get
    f32 = "f32", ScalarFamily.float, 4, F32Type.get
    f64 = "f64", ScalarFamily.float, 8, F64Type.get
    # Pas de Float80Type/Float128Type dans les bindings Python MLIR.
    f80 = "f80", ScalarFamily.float, 10
    f128 = "f128", ScalarFamily.float, 16
    idx = "index", ScalarFamily.idx, 8, IndexType.get

    def byte_size(self) -> int:
        return self._byte_size

    def get_kind(self) -> ScalarFamily:
        return self._family

    def get_type(self) -> Type:
        if self._make_type is None:
            raise ValueError(f"{self} non supporté par les bindings MLIR")
        return self._make_type()

    def _is_alias(self) -> bool:
        return self.name[:1].isupper()

    @staticmethod
    def from_type(attr: Type) -> Scalar | None:
        if isinstance(attr, IntegerType):
            for scalar in Scalar:
                if scalar._is_alias() or scalar.get_kind() is not ScalarFamily.int:
                    continue
                produced = scalar.get_type()
                if (
                    isinstance(produced, IntegerType)
                    and produced.width == attr.width
                ):
                    return scalar
            raise ValueError(f"Not supported {attr}")

        for scalar in Scalar:
            if scalar._make_type is None or scalar.get_kind() is ScalarFamily.int:
                continue
            if isinstance(attr, type(scalar.get_type())):
                return scalar
        return None
