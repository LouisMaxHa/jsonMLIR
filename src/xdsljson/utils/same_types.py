import pprint
from collections.abc import Sequence

from xdsljson.variables.val.val import ValNode


def same_types(
    lhs: Sequence[ValNode],
    rhs: Sequence[ValNode],
) -> bool:
    return (
        len(lhs) == len(rhs)
        and all(
            a.get_type() == b.get_type()
            for a, b in zip(lhs, rhs)
        )
    )

def assert_same_types(
    lhs: Sequence[ValNode],
    rhs: Sequence[ValNode],
) :
    assert len(lhs) == len(rhs), f"Should be same size {len(lhs)} vs {len(rhs)}"

    for i, l, r in zip(range(len(lhs)), lhs, rhs):
        if l.get_type() != r.get_type():
            raise ValueError(
                f"assert_same_type: Missmatch detected at indice {i}\n"
                f"lhs: {repr(l.get_type())}\n"
                f"rhs: {repr(r.get_type())}\n"
                f"\nVariables:\n"
                f"{pprint.pformat(vars(l))}\n"
                f"\n\n"
                f"{pprint.pformat(vars(r))}\n"
            )
