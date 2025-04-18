from abc import ABC
from typing import Self

from pydantic import BaseModel


class BaseModelWithSafeFields(BaseModel):
    @classmethod
    def create_from_dict(cls, data: dict) -> Self:
        return cls(**{k: v for k, v in data.items() if k in cls.model_fields})


class BaseCreateItemDTO(ABC, BaseModelWithSafeFields):
    ...


class BaseUpdateItemDTO(ABC, BaseModelWithSafeFields):
    ...


class BaseItemsListDTO(ABC, BaseModelWithSafeFields):
    id: int


class BaseItemDTO(ABC, BaseModelWithSafeFields):
    id: int
