from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from application.abstract.events import BaseEvent
from application.events.event_types import EventTypes
from application.finance.events import (
    BillConfirmedEvent,
    BillCreatedEvent,
    BillPaidEvent,
    BillPaymentEvent,
    BillRefundedEvent,
    TransactionCreatedEvent,
    TransactionStartBonusEvent,
    UsageCancelledEvent,
    UsageCreatedEvent,
)
from application.text.segment.events import (
    SegmentAiProcessingEvent,
    SegmentAiReceivedEvent,
    SegmentAiRequestedEvent,
    SegmentAiSavedEvent,
    SegmentCreateRequestedEvent,
    SegmentCreatedEvent,
)
from core.di.events import DIPublisher
from infrastructure.broker.event_outbox import (
    OUTBOX_STATUS_DEAD_LETTERED,
    OUTBOX_STATUS_FAILED,
    OUTBOX_STATUS_REPLAY_REQUESTED,
)
from infrastructure.repository.tortoise.models import EventOutboxModel


EVENT_MODEL_BY_TYPE: dict[str, Type[BaseEvent]] = {
    event_model.event_type.value: event_model
    for event_model in (
        SegmentCreateRequestedEvent,
        SegmentCreatedEvent,
        SegmentAiRequestedEvent,
        SegmentAiProcessingEvent,
        SegmentAiReceivedEvent,
        SegmentAiSavedEvent,
        BillCreatedEvent,
        BillPaymentEvent,
        BillPaidEvent,
        BillConfirmedEvent,
        BillRefundedEvent,
        UsageCreatedEvent,
        UsageCancelledEvent,
        TransactionCreatedEvent,
        TransactionStartBonusEvent,
    )
}


@dataclass(slots=True, frozen=True)
class EventOutboxOperationItem:
    id: int
    event_id: str
    event_type: str
    handler_group: str
    group_id: str | None
    pid: str | None
    status: str
    attempts: int
    error_message: str | None


class EventOutboxOperations:
    async def list_failed(
        self,
        *,
        limit: int = 50,
        statuses: tuple[str, ...] = (OUTBOX_STATUS_DEAD_LETTERED, OUTBOX_STATUS_FAILED),
    ) -> list[EventOutboxOperationItem]:
        rows = await EventOutboxModel.filter(status__in=statuses).order_by("-id").limit(limit)
        return [self._to_item(row) for row in rows]

    async def replay(self, outbox_id: int) -> EventOutboxOperationItem:
        outbox = await EventOutboxModel.get(id=outbox_id)
        event_model = self._event_model(outbox.event_type)
        payload = event_model.model_validate(outbox.payload)
        outbox.status = OUTBOX_STATUS_REPLAY_REQUESTED
        outbox.error_message = None
        await outbox.save()
        try:
            await DIPublisher[event_model, BaseEvent].publish(  # type: ignore[valid-type]
                payload=payload,
                group_id=outbox.group_id,
            )
        except Exception as exc:
            outbox.status = OUTBOX_STATUS_FAILED
            outbox.error_message = str(exc)
            await outbox.save()
            raise
        return self._to_item(outbox)

    @staticmethod
    def _event_model(event_type: str) -> Type[BaseEvent]:
        event_model = EVENT_MODEL_BY_TYPE.get(event_type)
        if event_model is None:
            raise ValueError(f"Unsupported outbox event type: {event_type}")
        return event_model

    @staticmethod
    def _to_item(row: EventOutboxModel) -> EventOutboxOperationItem:
        return EventOutboxOperationItem(
            id=row.id,
            event_id=row.event_id,
            event_type=row.event_type,
            handler_group=row.handler_group,
            group_id=row.group_id,
            pid=row.pid,
            status=row.status,
            attempts=row.attempts,
            error_message=row.error_message,
        )
