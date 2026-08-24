from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Literal

from jsonmlir.utils.discriminants import json_op_discriminator
from jsonmlir.operations.codegen import OpNode
from jsonmlir.operations.op_binary import binary_codegen
from jsonmlir.operations.op_constant import ConstOp
from jsonmlir.operations.op_operator import OperatorOp
from jsonmlir.utils.enum_scalars import Scalar, ScalarFamily
from jsonmlir.utils.trace import trace_step
from jsonmlir.variables.val.val import ValNode

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class UnaryOperator(Enum):
    negOp = "-"
    notOp = "!"


class UnaryOp(OpNode):
    """Opération unaire, réécrite en opération binaire avec une constante."""

    op: Literal["unary"] = json_op_discriminator("unary")
    ope: UnaryOperator
    value: BaseValue

    @trace_step("UnaryOp: {self.ope.value}")
    def codegen(self) -> Sequence[ValNode]:
        values = self.value.codegen()
        assert len(values) == 1, (
            f"Unary value expect one SSA value, got {len(values)} values."
        )

        type = values[0].get_type()
        scalar = Scalar.from_type(type)
        if scalar is None:
            raise TypeError(f"Operator {self.ope.value} not supported on {type}")
        is_float = scalar.get_kind() == ScalarFamily.float

        match self.ope.value:
            # -x  ->  x * -1
            case "-":
                ope = OperatorOp.timesFOp if is_float else OperatorOp.timesOp
                const = ConstOp(val=-1, type=scalar)

            # !x  ->  x xor 1, bascule le bit de poids faible
            case "!":
                if is_float:
                    raise TypeError(f"Operator ! not supported on {type}")
                ope = OperatorOp.xorOp
                const = ConstOp(val=1, type=scalar)

        return binary_codegen(ope, values, const.codegen())
