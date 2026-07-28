from collections.abc import Sequence
from typing import TypeGuard

from mlir.ir import Value


def all_ssavalues(
    seq: Sequence[str | Value],
) -> TypeGuard[Sequence[Value]]:
    return all(isinstance(x, Value) for x in seq)

def all_int(
    seq: Sequence[int | None],
) -> TypeGuard[Sequence[int]]:
    return all(isinstance(x, int) for x in seq)
