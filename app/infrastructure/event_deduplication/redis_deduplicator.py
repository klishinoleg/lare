import redis.asyncio as aioredis
from core.config import settings
from infrastructure.event_deduplication.base import BaseEventDeduplicatorService


class RedisDeduplicatorService(BaseEventDeduplicatorService):
    _redis = None

    @classmethod
    def get_redis(cls) -> aioredis.Redis:
        if cls._redis is None:
            cls._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return cls._redis

    async def is_duplicate(self, event_id: str) -> bool:
        redis = self.get_redis()
        key = f"event:{event_id}"
        exists = await redis.exists(key)
        if exists:
            return True
        await redis.set(key, "1", ex=3600)
        return False
