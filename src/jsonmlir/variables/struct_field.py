from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer, model_validator


class StructField(BaseModel):
    """Champ d'un ``define struct`` : sérialisé en JSON ``[name, type, offset, size]``."""

    model_config = ConfigDict(frozen=True)

    name: str
    type: Any  # TyNode union — résolu à l'exécution pour éviter les imports circulaires
    offset: int
    size: int

    @model_validator(mode="before")
    @classmethod
    def _from_json_array(cls, data: Any) -> Any:
        from jsonmlir.variables.ty.ty import parse_ty

        if isinstance(data, StructField):
            return data
        if isinstance(data, (list, tuple)) and len(data) == 4:
            field_name, field_type, offset, size = data
            return {
                "name": field_name,
                "type": parse_ty(field_type),
                "offset": offset,
                "size": size,
            }
        if isinstance(data, dict) and "type" in data and isinstance(data["type"], str):
            return {**data, "type": parse_ty(data["type"])}
        return data

    @model_serializer(mode="plain")
    def _serialize_json(self) -> list[Any]:
        from jsonmlir.variables.ty.ty import TyNodeBase, dump_ty

        ty = dump_ty(self.type) if isinstance(self.type, TyNodeBase) else self.type
        return [self.name, ty, self.offset, self.size]

    @property
    def NAME(self) -> str:
        return self.name

    @property
    def TYPE(self) -> Any:
        return self.type

    @property
    def OFFSET(self) -> int:
        return self.offset

    @property
    def SIZE(self) -> int:
        return self.size


FIELD_TYPE = StructField
