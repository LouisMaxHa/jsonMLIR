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


# Decorateur pour indiquer que cette méthode doit être affichée dans la trace disponible avec -T
def auto_log(log_format: str) -> Callable[[_F], _F]:
    def wrapper(func: _F) -> _F:
        setattr(func, "_log_format", log_format)
        return func
    return wrapper

# Valeur = Type + autres informations (addr mémoire, ...)
class ValNode(ABC, Generic[T]):
    ty: T

    # ──────────── Init ────────────
    @staticmethod
    @abstractmethod
    def init_from(type: TyNode, source: ValNode[Any]) -> ValNode[Any]:
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
    """Return the Json type of the value"""
    def get_ty(self) -> T:
        return self.ty

    """Return the MLIR type of the value"""
    def get_type(self) -> Type:
        return self.ty.get_type()

    def __repr__(self) -> str:
        return f"Val{self.get_ty()!r}"

    """Get value dimension, ([] for index, [1] for ptr, [x, y, ...] for array)"""
    @abstractmethod
    def get_dim(self) -> Sequence[Value]:
        raise NotImplementedError

    # ──────────── Get SSA ────────────
    """Return SSA value to pass to other other functions.
    This function can take index and will resolve the corresponding SSA value
    of the pointed elements."""
    def get_SSA(
        self, index: Sequence[str | Value | int]
    ) -> Value:

        if len(index) == 0:
            return self._get_SSA()
        return self.load(index)._get_SSA()

    """Internat version for get_SSA, called when index array is empty (base case of the recursive call on index)."""
    @abstractmethod
    def _get_SSA(
        self,
    ) -> Value:
        raise NotImplementedError

    # ──────────── Load ────────────
    # Same that get_ssa, but return Valnode
    def load(
        self,
        index: Sequence[str | Value | int],
    ) -> ValNode[Any]:
        return self._load(index_to_ssa(index))

    @auto_log("_load({index})")
    @abstractmethod
    def _load(
        self,
        index: Sequence[str | Value],
    ) -> ValNode[Any]:
        raise NotImplementedError

    # ──────────── Store ────────────
    # Same that load but to set element
    def store(
        self,
        index: Sequence[str | Value | int],
        source: ValNode[Any],
    ) -> None:
        return self._store(index_to_ssa(index), source)

    @auto_log("_store({index}, {source})")
    @abstractmethod
    def _store(
        self,
        index: Sequence[str | Value],
        source: ValNode[Any],
    ) -> None:
        raise NotImplementedError
