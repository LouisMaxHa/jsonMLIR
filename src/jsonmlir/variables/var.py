from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from mlir.ir import Type, Value

from jsonmlir.utils import ssa_val
from jsonmlir.utils.discard_builder import discard_builder
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.memory import variables_heap
from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNodeAny

if TYPE_CHECKING:
    from jsonmlir.operations.op_var import VarOp


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

    def get_val(self) -> ValNodeAny:
        if self.get_name() not in variables_heap.keys():
            raise ValueError(f"Variable {self.get_name()} not allocated, can't load.")

        return variables_heap[self.name]

    def get_type(self) -> Type:
        with discard_builder():
            return self.load().get_type()

    def get_indices(self) -> Sequence[str | Value]:
        index_ssa: Sequence[str | Value] = []

        for i in self.indices:
            if isinstance(i, str):
                index_ssa.append(i)
            elif isinstance(i, int):
                index_ssa.append(ssa_val.val_to_SSAValue(i, Scalar.idx))
            else:
                index_ssa.append(i.as_var().get_SSA())

        return index_ssa

    # ──────────── Overload ────────────
    def load(self) -> ValNodeAny:
        return self.get_val().load(self.get_indices())

    def store(self, value: ValNodeAny) -> None:
        return self.get_val().store(self.get_indices(), value)

    def get_SSA(self) -> Value:
        return self.get_val().get_SSA(self.get_indices())

    def init_from(self, type: TyNode, source: ValNodeAny) -> ValNodeAny:
        return self.get_val().init_from(type, source)
