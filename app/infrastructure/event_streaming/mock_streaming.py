import asyncio
from typing import AsyncGenerator
from application.events.streaming.types import StreamingTypes
from infrastructure.event_streaming.base import BaseEventStreaming
from application.events.streaming.dtos import EventStreamingDTO


class MockEventStreaming(BaseEventStreaming):
    """
    In-memory mock streaming backend for testing event status propagation.

    Use `publish()` to simulate new status updates.
    """

    def __init__(self, *args: tuple, streaming_type: StreamingTypes | None = None,
                 pid: str | None = None,
                 timeout: float | None = None) -> None:
        super().__init__(*args, streaming_type=streaming_type, timeout=timeout, pid=pid)
        self._event = asyncio.Event()
        self._status_queue: asyncio.Queue[EventStreamingDTO] = asyncio.Queue()

    async def _publish(self, key: str, event_streaming_dto: EventStreamingDTO) -> None:
        """
        Simulate publishing an event by adding it to the in-memory queue.
        """
        await self._status_queue.put(event_streaming_dto)
        self._event.set()

    async def _await_statuses(self, key: str) -> EventStreamingDTO:
        """
        Wait for a single expected status and return it.
        """
        while True:
            await self._event.wait()
            self._event.clear()

            while not self._status_queue.empty():
                dto: EventStreamingDTO = await self._status_queue.get()
                if dto.status in self._statuses:
                    return dto

    async def _streaming(self, key: str) -> AsyncGenerator[EventStreamingDTO, None]:
        """
        Yield each published status, and stop once an expected status is reached.
        """
        while True:
            await self._event.wait()
            self._event.clear()

            while not self._status_queue.empty():
                dto: EventStreamingDTO = await self._status_queue.get()
                yield dto
                if dto.status in self._statuses:
                    yield None
