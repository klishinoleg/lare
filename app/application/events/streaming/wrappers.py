from typing import Callable, Awaitable
from application.events.streaming.types import StreamingTypes
from core.di.events import DIEventStreaming
from infrastructure.event_streaming.base import BaseEventStreaming


def with_streaming(
        func: Callable[..., Awaitable[None]],
        streaming_type: StreamingTypes
) -> Callable[..., Awaitable[BaseEventStreaming]]:
    async def wrapper(*args: tuple, **kwargs: dict) -> BaseEventStreaming:
        event_streaming = DIEventStreaming.get(*args, streaming_type=streaming_type)
        await func(*args, pid=event_streaming.get_pid(), **kwargs)
        return event_streaming

    return wrapper
