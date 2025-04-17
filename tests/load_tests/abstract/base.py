from abc import ABC
from typing import Callable, Type
from pydantic import BaseModel
from domain.abstract import E
from application.abstract.dtos import BCIDTO


class BaseLoadTestAPI(ABC):
    route: str
    factory: Callable[[], E]
    init_create_dto: Type[BCIDTO]

    def get_create_payload(self) -> dict:
        """
        Generate one payload dict for POST /{route}/
        """
        entity = self.factory()
        dto: BaseModel = self.init_create_dto.create_from_dict(entity.to_dict(exclude_id=True))
        return dto.model_dump()
