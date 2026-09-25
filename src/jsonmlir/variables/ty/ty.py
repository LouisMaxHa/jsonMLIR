from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Annotated, Any, TypeAlias, cast

from mlir.ir import MemRefType, Type
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, TypeAdapter

from jsonmlir.utils.schema_shape import ast_schema_extra

"""Common ABC for value types (scalars, structs, and arrays).

Concrete types form a discriminated ``TyNode`` union on the ``type`` field.
Historical forms remain accepted through `parse_ty` at the JSON boundary.
"""

class TyNodeBase(BaseModel, ABC):
    """Base class for the discriminated ``TyNode`` type union.

    Pydantic validators accept compact JSON input and normalize it to the
    concrete type models. For example, the scalar shorthand is equivalent to
    its explicit form:

    .. code-block:: python

        # Scalar
        parse_ty("i64")
        parse_ty({"type": "scalar", "name": "i64"})

        # Ptr
        parse_ty({"addr": "i64"})
        parse_ty({"type": "ptr", "base": "i64"})

        # Struct
        parse_ty({"struct": "Real3"})
        parse_ty({"type": "struct", "name": "Real3})

        # Memref / Buffer / SOA
        parse_ty({"memref": [30, 30, "i64"]})
        parse_ty({"type": "memref", "dims" : [30, 30] "base": "i64"})
    """
    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra=ast_schema_extra,
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Allow instantiation using positionnal argument.
        Keep pydantic keyword only instantiation"""

        # No positionnal arguments
        if not args:
            super().__init__(**kwargs)
            return


        # Start by checking if we have the correct number of arguments
        # Type argument is constant, ignoring it.
        names = [f for f in type(self).model_fields if f != "type"]
        if len(args) > len(names):
                raise TypeError(
                    f"{type(self).__name__} accepts at most {len(names)} "
                    f"positional arguments, but received {len(args)}"
                )

        # Writtes args (unamed arguments) into named arguments
        for value, name  in zip(args, names):
            if name in kwargs:
                raise TypeError(
                    f"{type(self).__name__}: '{name}' supplied both positionally "
                    "and as a keyword"
                )
            kwargs[name] = value

        # Instanciate pydantic
        super().__init__(**kwargs)

    """Return the MLIR type (Arith.const, Memref)"""
    @abstractmethod
    def get_type(self) -> Type:
        """Return the corresponding MLIR value type."""
        raise NotImplementedError

    """Return the memref version of the value.
    Ex: Const are in fact memref<f64> rather than f64 to allow mutability"""
    @abstractmethod
    def get_memref_type(self) -> MemRefType:
        """Return the MLIR memref type used to store this value."""
        raise NotImplementedError

def dump_ty(value: TyNodeBase) -> Any:
    """Serialize a type in its canonical JSON form."""
    return value.model_dump(mode="json", by_alias=True)

def _coerce_ty_node(value: Any) -> Any:
    """Accept shorthand (``"i64"``) and legacy forms as ``TyNode`` field input."""
    if isinstance(value, TyNodeBase):
        return value
    if isinstance(value, str):
        return parse_ty(value)
    if isinstance(value, dict):
        return parse_ty(cast(dict[str, Any], value))
    return value


# Nested fields (``TyPtr.base``, ``TyMemref.base``): the same JSON coercion as
# ``TyNode``, without importing the union (which already contains TyPtr / TyMemref).

TyNested: TypeAlias = Annotated[TyNodeBase, BeforeValidator(_coerce_ty_node)]

# Concrete types are imported AFTER defining ``TyNodeBase`` / ``TyNested``:
# they inherit from them, and importing them earlier would create a circular
# import (``ty`` <-> ``ty_*``).

from jsonmlir.variables.ty.ty_buffer import TyBuffer
from jsonmlir.variables.ty.ty_mdspan import TyMdspan
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_not_supported import TyNotSupported
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_SOA import TySOA
from jsonmlir.variables.ty.ty_SSA import TySSA
from jsonmlir.variables.ty.ty_struct import TyStruct

union = Annotated[
    TyScalar
    | TyStruct
    | TyMemref
    | TyBuffer
    | TySOA
    | TyPtr
    | TySSA
    | TyMdspan
    | TyNotSupported,
    Field(discriminator="type"),
]

# LMX Is this really necessary?
_ty_adapter_instance: TypeAdapter[Any] | None = None
def _get_ty_union_adapter() -> TypeAdapter[Any]:
    global _ty_adapter_instance
    if _ty_adapter_instance is None:
        _ty_adapter_instance = TypeAdapter(union)
    return _ty_adapter_instance

# LMX FIN


if TYPE_CHECKING:
    TyNode: TypeAlias = union
    TyNested: TypeAlias = TyNode
else:
    TyNode: TypeAlias = Annotated[union, BeforeValidator(_coerce_ty_node)]


"""Build the type corresponding to a JSON description."""
def parse_ty(value: Any | TyNode) -> TyNode:
    """Parse a canonical or legacy type description.

    Strings such as ``"i64"`` and legacy dictionaries are normalized to the
    discriminated type model used by the compiler.

    Compact forms include ``"i64"`` for a scalar, ``{"addr": ...}`` for a
    pointer, and ``{"memref": [dimensions, base]}`` for a memref. Nested type
    fields accept the same shorthand.

    Args:
        value: A type model, scalar type name, or JSON-compatible dictionary.

    Returns:
        The corresponding typed node.
    """

    # If the value implements TyNodeBase, cast it to the TyNode class union.
    if isinstance(value, TyNodeBase):
        return cast(TyNode, value)

    def convert_to_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, str):
            return {"type": "scalar", "name": value}

        elif isinstance(value, dict):
            value_dict = cast(dict[str, Any], value)
            if "type" in value_dict:
                return value_dict

            if "addr" in value_dict:
                return {"type": "ptr", "base": value_dict["addr"]}

            if "struct" in value_dict:
                return {"type": "struct", "name": value_dict["struct"]}

            for kind in ("memref", "soa", "buffer"):
                if kind in value_dict:
                    raw = cast(list[Any], value_dict[kind])
                    dimensions, base = raw[:-1], raw[-1]
                    return {"type": kind, "dims": dimensions, "base": base}

        return {"type": "notSupported", "msg":value}

    return _get_ty_union_adapter().validate_python(convert_to_dict(value))
