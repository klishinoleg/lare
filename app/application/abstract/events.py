from functools import wraps
from pydantic import BaseModel, Field
from application.events.event_types import EventTypes
from abc import ABC, abstractmethod
from typing import ClassVar, Any, Callable, Awaitable, Type, Self, TypeVar
from uuid import UUID, uuid4
from application.events.handler_groups import HandlerGroups
from core.di.deduplicator import DIDeduplicator
from core.di.events import DIPublisher, DIEventStreaming


class BaseEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    pid: str | None = None
    event_type: ClassVar[EventTypes]

    def get_message(self) -> str:
        return ""


class BaseErrorEvent[ET: EventTypes](BaseEvent):
    step: ET
    error_message: str
    traceback: str | None = None
    is_expected: bool = False

    def get_message(self) -> str:
        return self.error_message


E = TypeVar("E", bound=BaseErrorEvent)


class BaseEventHandler[BE: BaseEvent, BEErr: BaseErrorEvent](ABC):
    event_type: EventTypes
    event_handler_group: HandlerGroups = HandlerGroups.MAIN

    @classmethod
    @abstractmethod
    async def handler(cls, event: BE) -> None:
        ...

    @classmethod
    async def execute(cls, event: BE) -> None:
        deduplicator = DIDeduplicator.get()
        if await deduplicator.is_duplicate(f"{cls.event_handler_group}_{event.id}"):
            return
        await cls.handler(event)

    @staticmethod
    def with_streaming(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(self_or_cls: Self, event: BE) -> None:
            if event.pid:
                await DIEventStreaming.get(pid=event.pid).publish_event(event)
            return await func(self_or_cls, event)

        return wrapper

    @classmethod
    def with_error(cls, error_model: Type[BEErr], expected_errors: list[Type[E]] | None = None) -> Callable:
        def decorator(func: Callable[[Any, BE], Awaitable[None]]) -> Callable:
            @wraps(func)
            async def wrapper(self_or_cls: Self, event: BE) -> None:
                try:
                    await func(cls, event)
                except Exception as ex:
                    event_data = event.model_dump()
                    additional_data = {
                        field: event_data.get(field)
                        for field in error_model.model_fields.keys()
                        if field not in ["step", "id"] and field in event_data
                    }
                    await DIPublisher[error_model, error_model].publish_error(
                        event_error_model=error_model,
                        ex=ex,
                        step=event.event_type,
                        **additional_data,
                        is_expected=expected_errors and any([isinstance(ex, err) for err in expected_errors])
                    )
                    raise

            return wrapper

        return decorator
