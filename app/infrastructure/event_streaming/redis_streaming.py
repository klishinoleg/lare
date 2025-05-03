from typing import AsyncGenerator
from redis import asyncio, Redis
import json
from redis.client import PubSub
from application.events.streaming.dtos import EventStreamingDTO
from core.config import settings
from infrastructure.event_streaming.base import BaseEventStreaming


class RedisEventStreaming(BaseEventStreaming):
    """
    Redis-based PubSub service for event streaming.
    """
    redis: Redis
    pubsub: PubSub

    async def connect(self) -> None:
        if not hasattr(self, "redis"):
            self.redis = await asyncio.from_url(settings.redis_event_streaming_url, decode_responses=True)

    async def _publish(self, key: str, event_streaming_dto: EventStreamingDTO) -> None:
        await self.connect()
        payload = json.dumps(event_streaming_dto.model_dump())
        await self.redis.publish(key, payload)

    async def _await_statuses(self, key: str) -> EventStreamingDTO | None:
        await self.connect()
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(key)
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                dto = EventStreamingDTO.model_validate(data)
                if dto.status in self._statuses:
                    await self.pubsub.unsubscribe(key)
                    return dto
        return None

    async def _streaming(self, key: str) -> AsyncGenerator[EventStreamingDTO, None]:
        """
        Async generator that yields each status update for the given key.

        Yields:
            EventStreamingDTO
        """
        await self.connect()
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe(key)
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    dto = EventStreamingDTO.model_validate(data)
                    yield dto
                    if dto.status in self._statuses:
                        yield None
        finally:
            await self.pubsub.unsubscribe(key)

    async def _on_timeout(self, key: str) -> None:
        await self.pubsub.unsubscribe(key)
        await super()._on_timeout(key)
