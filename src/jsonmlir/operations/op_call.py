from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from mlir.dialects.func import CallOp as MLIRCallOp
from mlir.ir import Value

from jsonmlir.operations.codegen import OpNode
from jsonmlir.trace import trace_step
from jsonmlir.variables.memory import functions_registry
from jsonmlir.variables.val.val import ValNode
from jsonmlir.variables.val.val_SSA import ValSSA

if TYPE_CHECKING:
    from jsonmlir.operations.base import BaseValue


class CallOp(OpNode):
    """Appel d'une fonction déclarée via DefineFunctionOp.

    Les types de retour et la vérification des types d'arguments sont
    résolus automatiquement depuis le registre global des fonctions.
    """

    op: Literal["call"] = "call"
    name: str
    args: Sequence[BaseValue] = ()

    @trace_step("CallOp: {self.name}")
    def codegen(self) -> Sequence[ValNode]:
        sig = functions_registry.get(self.name)
        if sig is None:
            raise ValueError(
                f"Fonction '{self.name}' non déclarée. "
                "Utilisez DefineFunction dans le module avant de l'appeler."
            )

        # Évaluation des arguments
        arg_ssas: list[Value] = []
        arg_vals: list[ValNode] = []
        for arg in self.args:
            vals = arg.codegen()
            arg_vals.extend(vals)
            for val in vals:
                arg_ssas.append(val.get_SSA([]))

        # Vérification du nombre d'arguments
        if len(arg_ssas) != len(sig.args):
            raise TypeError(
                f"Fonction '{self.name}' attend {len(sig.args)} argument(s), "
                f"{len(arg_ssas)} fourni(s)."
            )

        # Vérification des types d'arguments
        for i, (val, (_arg_name, expected_ty)) in enumerate(zip(arg_vals, sig.args)):
            actual_type = val.get_type()
            expected_type = expected_ty.get_type()
            if actual_type != expected_type:
                raise TypeError(
                    f"Argument {i} de '{self.name}' : "
                    f"type attendu {expected_type}, reçu {actual_type}."
                )

        # Types de retour depuis le registre
        mlir_return_types = [ty.get_type() for ty in sig.return_types]

        call_op = MLIRCallOp(mlir_return_types, self.name, arg_ssas)

        return [ValSSA(res) for res in call_op.results]
