from infrastructure.event_deduplication.base import BaseEventDeduplicatorService
from infrastructure.event_deduplication.redis_deduplicator import RedisDeduplicatorService
from core.config import settings
from core.enums.storage.deduplicator import DeduplicatorTypes


class DIDeduplicator:
    @staticmethod
    def get() -> BaseEventDeduplicatorService:
        if settings.deduplicator_type == DeduplicatorTypes.REDIS:
            return RedisDeduplicatorService()
        else:
            raise AttributeError(f"Deduplicator {settings.deduplicator_type} not found")
