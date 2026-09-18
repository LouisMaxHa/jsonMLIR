import pprint
from collections.abc import Iterable, Sequence
from typing import Any

from mlir.ir import ShapedType, Type

from jsonmlir.variables.ty.ty import TyNode
from jsonmlir.variables.val.val import ValNode


def assert_same_shape(
    lhs: Iterable[int],
    rhs: Iterable[int]
) :
    if(list(lhs) != list(rhs)):
        ValueError(f"Ty shape {lhs} donc match given SSA shape {rhs}".replace(
            str(ShapedType.get_dynamic_size()), "DYNAMIC_INDEX"
        ))

def assert_same_ty_strict(lhs: TyNode, rhs: TyNode):
    """Compare if value are stricly identicall.

    Strict because a TySSA(addr) can have in his addr a TyScalar() or something alse,
    In this case, the comparison will failed
    """
    assert lhs == rhs, f"type {lhs} does not match expected {rhs}"

def assert_same_type(lhs: Type, rhs: Type):
    assert lhs != rhs, f"type {lhs} does not match expected {rhs}"

def assert_same_val(
    lhs: ValNode[Any],
    rhs: ValNode[Any],
    indice: int = -1
) :
    if lhs.get_type() != rhs.get_type():
        raise ValueError(
            f"assert_same_type: Missmatch detected {'' if indice == -1 else 'at indice ' + str(indice)}\nlhs: {repr(lhs.get_type())}\nrhs: {repr(rhs.get_type())}\n\nvariables:\n{pprint.pformat(vars(lhs))}\n{pprint.pformat(vars(rhs))}\n"  # noqa: E501
        )

def assert_same_vals(
    lhs: Sequence[ValNode[Any]],
    rhs: Sequence[ValNode[Any]],
) :
    assert len(lhs) == len(rhs), f"Should be same size {len(lhs)} vs {len(rhs)}"
    for i, (l, r) in enumerate(zip(lhs, rhs)):
        assert_same_val(l, r, i)
