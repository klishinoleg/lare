from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentAiRequestedEvent, SegmentCreatedEvent, SegmentErrorEvent
from application.text.segment.services.segment_ai_log_service import SegmentAiLogService
from core.di.events import DIPublisher


class SegmentCreatedHandler(BaseEventHandler[SegmentCreatedEvent, SegmentErrorEvent]):
    """
    Handles post-creation logic after a segment has been successfully created.
    """
    event_type = SegmentCreatedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentCreatedEvent) -> None:
        ai_log = await SegmentAiLogService().ensure_request_log(
            account_id=event.account_id,
            segment_id=event.segment_id,
            ai_model=event.ai_model,
            action=event.action,
            translate_type=event.translate_type,
        )
        await DIPublisher[SegmentAiRequestedEvent, SegmentErrorEvent].publish(
            payload=SegmentAiRequestedEvent(
                account_id=event.account_id,
                segment_id=event.segment_id,
                ai_log_id=ai_log.id,
                ai_model=event.ai_model,
                action=event.action,
                translate_type=event.translate_type,
                pid=event.pid,
            ),
            group_id=f"account:{event.account_id}",
        )
