from pydantic import BaseModel, Field
from application.events.event_types import ChapterEventTypes
from abc import ABC, abstractmethod
from typing import ClassVar, Any
from uuid import UUID, uuid4

from application.events.handler_groups import HandlerGroups
from core.di.deduplicator import DIDeduplicator


class BaseEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    event_type: ClassVar[ChapterEventTypes]


class BaseErrorEvent(BaseEvent):
    step: ChapterEventTypes
    error_message: str
    traceback: str | None = None


class BaseEventHandler[BE: BaseEvent](ABC):
    event_type: ChapterEventTypes
    event_handler_group: HandlerGroups = HandlerGroups.MAIN

    @classmethod
    @abstractmethod
    async def handler(cls, event: BE, group_id: int | None) -> None:
        ...

    @classmethod
    async def execute(cls, event: Any, group_id: int | None = None, **kwargs: dict) -> None:
        deduplicator = DIDeduplicator.get()
        if await deduplicator.is_duplicate(event.id):
            return
        await cls.handler(event, group_id=group_id)
