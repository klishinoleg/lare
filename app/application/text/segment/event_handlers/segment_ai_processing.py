from application.ai.reader_provider import ReaderSegmentRequest, get_reader_ai_provider
from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentAiProcessingEvent, SegmentAiReceivedEvent, SegmentErrorEvent
from application.text.segment.services.segment_ai_log_service import SegmentAiLogService
from application.text.segment.services.segment_crud_service import SegmentCrudService
from core.di.events import DIPublisher


class SegmentAiProcessingHandler(BaseEventHandler[SegmentAiProcessingEvent, SegmentErrorEvent]):
    """
    Handles the intermediate processing status from AI provider (e.g., while waiting).
    """
    event_type = SegmentAiProcessingEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentAiProcessingEvent) -> None:
        segment = await SegmentCrudService().get_by_id(event.segment_id)
        response = await get_reader_ai_provider().process_segment(
            ReaderSegmentRequest(
                account_id=event.account_id,
                segment_id=event.segment_id,
                ai_log_id=event.ai_log_id,
                ai_model=event.ai_model,
                text=segment.name,
                language_id=segment.language_id,
                action=event.action,
                translate_type=event.translate_type,
                query_id=event.query_id,
                pid=event.pid,
            )
        )
        content = response.content

        await SegmentAiLogService().save_response(
            ai_log_id=event.ai_log_id,
            content=content,
            action=event.action,
        )
        await DIPublisher[SegmentAiReceivedEvent, SegmentErrorEvent].publish(
            payload=SegmentAiReceivedEvent(
                account_id=event.account_id,
                segment_id=event.segment_id,
                ai_log_id=event.ai_log_id,
                content=content,
                action=event.action,
                translate_type=event.translate_type,
                pid=event.pid,
            ),
            group_id=f"account:{event.account_id}",
        )
