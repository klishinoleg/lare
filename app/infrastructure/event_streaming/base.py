import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, TYPE_CHECKING
from application.events.streaming.map import get_streaming_status
from application.events.streaming.dtos import EventStreamingDTO
from application.events.streaming.exceptions import StreamingTimeoitException
from application.events.streaming.statuses import StreamingStatuses
from application.events.streaming.types import StreamingTypes
from core.config import settings
from core.messages.exceptions import GetExMessages

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent


class BaseEventStreaming[BE: "BaseEvent"](ABC):
    """
    Abstract PubSub service for publishing and subscribing to events.

    This service should allow:
    - Publishing status changes for a given key (pid).
    - Subscribing and waiting for status changes.
    """
    _pid: str | None = None
    _timeout: float = settings.event_streaming_timeout

    def __init__(self, *args: tuple[int, ...], streaming_type: StreamingTypes | None = None, pid: str | None = None,
                 timeout: float | None = None):
        if streaming_type:
            timestamp = str(datetime.now().timestamp())
            self._pid = f"{streaming_type.value}:{":".join(map(str, args))}:{timestamp}"
        else:
            self._pid = pid
        self._statuses: tuple[StreamingStatuses, ...] = (
            StreamingStatuses.SUCCEEDED.value,
            StreamingStatuses.FAILED.value
        )
        self._timeout = timeout if timeout is not None else settings.event_streaming_timeout

    def get_pid(self) -> str | None:
        return self._pid

    @abstractmethod
    async def _publish(self, key: str, event_streaming_dto: EventStreamingDTO) -> None:
        """
        Publish a new status for the given key.

        Args:
            key (str): The event key, e.g., start_bonus:{account_id}:{pid}.
            :param event_streaming_dto:
            :param key:
        """
        ...

    @abstractmethod
    async def _await_statuses(self, key: str) -> EventStreamingDTO:
        """
        Wait until a status change occurs for the given key.

        Args:
            :param key:
        Returns:
            EventStreamingDTO
        """
        ...

    @abstractmethod
    async def _streaming(self, key: str) -> AsyncGenerator[EventStreamingDTO, None]:
        """
        Async generator that yields each status update for the given key.

        Yields:
            EventStreamingDTO
        """
        ...

    def set_pid(self, pid: str) -> None:
        self._pid = pid

    async def publish_event(self, event: BE) -> None:
        if not self._pid:
            return
        streaming_type = StreamingTypes(self._pid.split(":")[0])
        if not self._pid:
            return
        status = get_streaming_status(streaming_type, event)
        if not status:
            return
        await self._publish(self._pid, EventStreamingDTO(status=status, message=event.get_message()))

    async def await_statuses(self, statuses: tuple[StreamingStatuses, ...] | None = None,
                             timeout: float | None = None) -> EventStreamingDTO:
        if not self._pid:
            raise ValueError("PID is not set. Cannot await event stream.")
        if timeout:
            self._timeout = timeout
        if statuses:
            self._statuses = statuses
        try:
            return await asyncio.wait_for(self._await_statuses(self._pid), timeout=self._timeout)
        except asyncio.TimeoutError:
            await self._on_timeout(self._pid)

    async def streaming(self, statuses: tuple[StreamingStatuses, ...] | None = None,
                        timeout: float | None = None) -> AsyncGenerator[EventStreamingDTO, None]:
        if not self._pid:
            raise ValueError("PID is not set. Cannot await event stream.")
        if statuses:
            self._statuses = statuses
        if timeout:
            self._timeout = timeout

        inner_stream = await self._streaming(self._pid)

        async def generator_wrapper() -> AsyncGenerator[EventStreamingDTO, None]:
            try:
                async for item in inner_stream:
                    try:
                        yield await asyncio.wait_for(asyncio.sleep(0, result=item), timeout=self._timeout)
                    except asyncio.TimeoutError:
                        await self._on_timeout(self._pid)
                        return
            finally:
                await inner_stream.aclose()

        return generator_wrapper()

    async def _on_timeout(self, key: str | None) -> None:
        raise StreamingTimeoitException(GetExMessages.event_streaming_timeout(key, self._timeout))
