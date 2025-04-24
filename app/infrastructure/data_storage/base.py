from abc import ABC, abstractmethod
from pathlib import Path


class BaseDataStorage[DT: list | dict, PT: str | Path](ABC):

    @abstractmethod
    async def save_json(self, path: PT, data: DT) -> None:
        ...

    @abstractmethod
    async def save_text(self, path: PT, text: str) -> None:
        ...

    @abstractmethod
    async def load_json(self, path: PT) -> DT:
        ...

    @abstractmethod
    async def load_text(self, path: PT) -> str:
        ...
