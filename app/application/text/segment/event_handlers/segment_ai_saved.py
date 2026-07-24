from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.finance.dtos.acount_usage import CreateAccountUsageDTO
from application.finance.utils.usage_factory import create_usage_event
from application.text.segment.events import SegmentAiSavedEvent, SegmentErrorEvent
from application.text.segment.services.segment_crud_service import SegmentCrudService
from decimal import Decimal
from domain.finance.enums.account_usage_type import AccountUsageType
from domain.text_data.enums import TextActionsTypes


class SegmentAiSavedHandler(BaseEventHandler[SegmentAiSavedEvent, SegmentErrorEvent]):
    """
    Confirms that the AI result (text or audio) has been saved and is accessible.
    """
    event_type = SegmentAiSavedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentAiSavedEvent) -> None:
        segment = await SegmentCrudService().get_by_id(event.segment_id)
        usage_amount = max(1, len(segment.name.split()))
        usage_type = (
            AccountUsageType.AI_VOICE
            if event.action == TextActionsTypes.VOICE
            else AccountUsageType.AI_TRANSLATE
        )
        await create_usage_event(
            CreateAccountUsageDTO(
                account_id=event.account_id,
                usage_type=usage_type,
                usage_id=event.segment_id,
                usage_amount=usage_amount,
                credits_amount=Decimal(usage_amount),
            ),
            pid=event.pid,
        )
