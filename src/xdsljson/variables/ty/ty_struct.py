from dataclasses import dataclass

from mlir.ir import MemRefType

from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.memory import STRUCTS_TYPE, structs_type
from xdsljson.variables.ty.ty import TyNode


# Init in frozen dataclass : https://stackoverflow.com/a/58336722
@dataclass(frozen=True, init=False)
class TyStruct(TyNode):
    _name: str | None
    _resolved: STRUCTS_TYPE | None

    @property
    def struct(self) -> STRUCTS_TYPE:
        if self._resolved is not None:
            return self._resolved
        if self._name is None or self._name not in structs_type:
            raise ValueError(f"Struct {self._name!r} is not defined")
        return structs_type[self._name]

    def get_type(self) -> MemRefType:
        return MemRefType.get([self.struct.SIZE], Scalar.i8.get_type())

    def get_memref_type(self) -> MemRefType:
        return self.get_type()

    def __repr__(self) -> str:
        name = self._name
        if name is None and self._resolved is not None:
            name = self._resolved.NAME
        return f"Struct({name!r})"

    def __init__(self, base: str | STRUCTS_TYPE):
        # str
        if isinstance(base, str):
            object.__setattr__(self, "_name", base)
            object.__setattr__(self, "_resolved", structs_type.get(base))
            return

        # struct
        object.__setattr__(self, "_name", base.NAME)
        object.__setattr__(self, "_resolved", base)
