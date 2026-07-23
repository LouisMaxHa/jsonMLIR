from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mlir.ir import InsertionPoint, Type, Value

from xdsljson.trace import trace_step
from xdsljson.utils.ssa_dim import index_to_ssa
from xdsljson.variables.ty.ty import TyNode


def auto_log(log_format):
    def wrapper(func):
        func._log_format = log_format
        return func
    return wrapper

class ValNode(ABC):


    # ──────────── Init ────────────
    @staticmethod
    @abstractmethod
    def init_from(type: TyNode, source: ValNode, ip: InsertionPoint) -> ValNode:
        raise NotImplementedError

    # Plutôt content de celui-la :)
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in cls.__dict__.items():
            parent_method = getattr(super(cls, cls), name, None)
            if not callable(method):
                continue

            log_format = getattr(parent_method, "_log_format", None)
            if not isinstance(log_format, str) :
                continue

            wrapped = trace_step(f"{cls.__name__}." + log_format)(method)
            setattr(cls, name, wrapped)

    # ──────────── Getter ────────────
    @abstractmethod
    def get_ty(self) -> TyNode:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"Val{self.get_ty()!r}"

    @abstractmethod
    def get_type(self) -> Type:
        raise NotImplementedError

    @abstractmethod
    def get_dim(self, ip: InsertionPoint) -> Sequence[Value]:
        raise NotImplementedError

    def get_SSA(
        self, index: Sequence[str | Value | int], ip: InsertionPoint
    ) -> Value:

        if len(index) == 0:
            return self._get_SSA(ip)
        return self.load(index, ip)._get_SSA(ip)

    @abstractmethod
    def _get_SSA(
        self,
        ip: InsertionPoint,
    ) -> Value:
        raise NotImplementedError

    # ──────────── Load ────────────
    def load(
        self,
        index: Sequence[str | Value | int],
        ip: InsertionPoint,
    ) -> ValNode:
        return self._load(index_to_ssa(index, ip), ip)

    @auto_log("_load({index})")
    @abstractmethod
    def _load(
        self,
        index: Sequence[str | Value],
        ip: InsertionPoint,
    ) -> ValNode:
        raise NotImplementedError

    # ──────────── Store ────────────
    def store(
        self,
        index: Sequence[str | Value | int],
        source: ValNode,
        ip: InsertionPoint,
    ) -> None:
        return self._store(index_to_ssa(index, ip), source, ip)

    @auto_log("_store({index}, {source})")
    @abstractmethod
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
        ip: InsertionPoint,
    ) -> None:
        raise NotImplementedError
