from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mlir.ir import Type, Value

from jsonmlir.trace import trace_step
from jsonmlir.utils.ssa_dim import index_to_ssa
from jsonmlir.variables.ty.ty import TyNode


def auto_log(log_format):
    def wrapper(func):
        func._log_format = log_format
        return func
    return wrapper

class ValNode(ABC):


    # ──────────── Init ────────────
    @staticmethod
    @abstractmethod
    def init_from(type: TyNode, source: ValNode) -> ValNode:
        raise NotImplementedError

    # Plutôt content de celui-la :)
    # L'idée est d'insérer automatiquement des trace-step sur nos opérateurs
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, method in cls.__dict__.items():
            parent_method = getattr(super(cls, cls), name, None)

            # On annote trace step que si c'est une méthode
            if not callable(method):
                continue

            # On récupère le log format définis par le parent
            log_format = getattr(parent_method, "_log_format", None)
            if not isinstance(log_format, str) :
                continue

            # On wrappe la méthode de la classe enfant en rajoutant non de classe + log_format
            wrapped = trace_step(f"{cls.__name__}." + log_format, display_entry=True)(method)
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
    def get_dim(self) -> Sequence[Value]:
        raise NotImplementedError

    def get_SSA(
        self, index: Sequence[str | Value | int]
    ) -> Value:

        if len(index) == 0:
            return self._get_SSA()
        return self.load(index)._get_SSA()

    @abstractmethod
    def _get_SSA(
        self,
    ) -> Value:
        raise NotImplementedError

    # ──────────── Load ────────────
    def load(
        self,
        index: Sequence[str | Value | int],
    ) -> ValNode:
        return self._load(index_to_ssa(index))

    @auto_log("_load({index})")
    @abstractmethod
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode:
        raise NotImplementedError

    # ──────────── Store ────────────
    def store(
        self,
        index: Sequence[str | Value | int],
        source: ValNode,
    ) -> None:
        return self._store(index_to_ssa(index), source)

    @auto_log("_store({index}, {source})")
    @abstractmethod
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode,
    ) -> None:
        raise NotImplementedError
