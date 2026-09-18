from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from jsonmlir.operations.op_binary import BinaryOp
from jsonmlir.variables.val.val import ValNode

METHODE_REGISTER: dict[Any, Any] = {}

# Ope
def opeAddReal3(op: BinaryOp) -> Sequence[ValNode[Any]]:
  assert(len(op.lhs) == 1)

  # Check struct name is real3

  # Alloc new struct

  # Add .x .y .z to this struct

  # Return the struct

