from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any, Generic, TypeVar

from mlir.ir import Type, Value

from jsonmlir.utils.ssa_dim import index_to_ssa
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.ty.ty import TyNode, TyNodeBase

T = TypeVar("T", bound=TyNodeBase)
_F = TypeVar("_F", bound=Callable[..., Any])


def auto_log(log_format: str) -> Callable[[_F], _F]:
    def wrapper(func: _F) -> _F:
        setattr(func, "_log_format", log_format)
        return func
    return wrapper

class ValNode(ABC, Generic[T]):
    ty: T

    # ──────────── Init ────────────
    @staticmethod
    @abstractmethod
    def init_from(type: TyNode, source: ValNodeAny) -> ValNodeAny:
        raise NotImplementedError

    # Plutôt content de celui-la :)
    # L'idée est d'insérer automatiquement des trace-step sur nos opérateurs
    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        for name, method in cls.__dict__.items():
            parent_method = getattr(super(cls, cls), name, None)

            # Si c'est une méthode
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
    def get_ty(self) -> T:
        return self.ty

    def __repr__(self) -> str:
        return f"Val{self.get_ty()!r}"

    def get_type(self) -> Type:
        return self.ty.get_type()

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
    ) -> ValNodeAny:
        return self._load(index_to_ssa(index))

    @auto_log("_load({index})")
    @abstractmethod
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNodeAny:
        raise NotImplementedError

    # ──────────── Store ────────────
    def store(
        self,
        index: Sequence[str | Value | int],
        source: ValNodeAny,
    ) -> None:
        return self._store(index_to_ssa(index), source)

    @auto_log("_store({index}, {source})")
    @abstractmethod
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNodeAny,
    ) -> None:
        raise NotImplementedError


# Un nœud dont le type statique est inconnu (collections hétérogènes,
# résultats de codegen, etc.). ``ValNode`` est invariant en ``T`` (attribut
# ``ty`` mutable) : ``Any`` est le seul paramètre acceptant tous les
# ``ValNode[TyX]`` concrets.
ValNodeAny = ValNode[Any]
