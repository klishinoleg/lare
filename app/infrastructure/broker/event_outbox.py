from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.config import settings
from tortoise import Tortoise

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent

OUTBOX_STATUS_PROCESSING = "processing"
OUTBOX_STATUS_PROCESSED = "processed"
OUTBOX_STATUS_FAILED = "failed"
OUTBOX_STATUS_DEAD_LETTERED = "dead_lettered"
OUTBOX_STATUS_REPLAY_REQUESTED = "replay_requested"


class EventOutboxRecorder:
    @staticmethod
    def max_attempts() -> int:
        return max(1, settings.event_outbox_max_attempts)

    @staticmethod
    def _tortoise_ready() -> bool:
        return bool(getattr(Tortoise, "_inited", False))

    @staticmethod
    def _payload_data(payload: BaseEvent) -> dict[str, Any]:
        try:
            return payload.model_dump(mode="json")
        except Exception:
            return {"id": str(payload.id), "event_type": payload.event_type.value}

    @classmethod
    async def start(
        cls,
        payload: BaseEvent,
        handler_group: str,
        group_id: str | None,
    ) -> Any | None:
        if (
            not cls._tortoise_ready()
            or not hasattr(payload, "id")
            or not hasattr(payload, "event_type")
        ):
            return None

        from infrastructure.repository.tortoise.models import EventOutboxModel

        outbox, _ = await EventOutboxModel.get_or_create(
            event_id=str(payload.id),
            handler_group=handler_group,
            defaults={
                "event_type": payload.event_type.value,
                "group_id": group_id,
                "pid": payload.pid,
                "payload": cls._payload_data(payload),
            },
        )
        outbox.event_type = payload.event_type.value
        outbox.group_id = group_id
        outbox.pid = payload.pid
        outbox.payload = cls._payload_data(payload)
        outbox.status = OUTBOX_STATUS_PROCESSING
        outbox.attempts += 1
        outbox.error_message = None
        await outbox.save()
        return outbox

    @classmethod
    def attempts_exhausted(cls, outbox: Any | None) -> bool:
        return bool(outbox is not None and outbox.attempts >= cls.max_attempts())

    @staticmethod
    async def finish(
        outbox: Any | None,
        status: str,
        error_message: str | None = None,
    ) -> None:
        if outbox is None:
            return
        outbox.status = status
        outbox.error_message = error_message
        await outbox.save()
