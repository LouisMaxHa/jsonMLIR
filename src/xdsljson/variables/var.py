from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from mlir.ir import InsertionPoint, Type, Value

from xdsljson.utils import ssa_val
from xdsljson.utils.discard_builder import discard_builder
from xdsljson.utils.enum_scalars import Scalar
from xdsljson.variables.memory import variables_heap
from xdsljson.variables.ty.ty import TyNode
from xdsljson.variables.val.val import ValNode

if TYPE_CHECKING:
    from xdsljson.operations.op_var import VarOp


class Var:
    name: str
    indices: Sequence[int | str | VarOp]
    type: TyNode | None = None

    def __init__(
        self, name: str, indices: Sequence[int | str | VarOp], type: TyNode | None
    ):
        self.name = name
        self.indices = indices
        self.type = type

    def get_name(self) -> str:
        return self.name

    def get_ty(self) -> TyNode:
        given_type = self.type
        saved_type: TyNode | None = None
        if self.get_name() in variables_heap.keys():
            saved_type = variables_heap[self.get_name()].get_ty()

        match (given_type is None, saved_type is None):
            case (True, True):
                raise Exception(f"Can't find type for {repr(self.name)}")
            case (True, False):
                assert saved_type is not None
                return saved_type
            case (False, True):
                assert given_type is not None
                return given_type
            case (False, False):
                assert given_type is not None
                assert saved_type is not None
                assert type(saved_type) is type(given_type)
                return saved_type

    def get_val(self) -> ValNode:
        if self.get_name() not in variables_heap.keys():
            raise ValueError(f"Variable {self.get_name()} not allocated, can't load.")

        return variables_heap[self.name]

    def get_type(self) -> Type:
        return self.load(discard_builder()).get_type()

    def get_indices(self, ip: InsertionPoint) -> Sequence[str | Value]:
        index_ssa: Sequence[str | Value] = []

        for i in self.indices:
            if isinstance(i, str):
                index_ssa.append(i)
            elif isinstance(i, int):
                index_ssa.append(ssa_val.val_to_SSAValue(i, Scalar.idx, ip))
            else:
                index_ssa.append(i.as_var().get_SSA(ip))

        return index_ssa

    # ──────────── Overload ────────────
    def load(self, ip: InsertionPoint) -> ValNode:
        return self.get_val().load(self.get_indices(ip), ip)

    def store(self, value: ValNode, ip: InsertionPoint) -> None:
        return self.get_val().store(self.get_indices(ip), value, ip)

    def get_SSA(self, ip: InsertionPoint) -> Value:
        return self.get_val().get_SSA(self.get_indices(ip), ip)

    def init_from(self, type: TyNode, source: ValNode, ip: InsertionPoint) -> ValNode:
        return self.get_val().init_from(type, source, ip)
