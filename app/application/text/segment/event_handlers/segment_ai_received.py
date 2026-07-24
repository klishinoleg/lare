from application.abstract.events import BaseEventHandler
from application.events.handler_groups import HandlerGroups
from application.text.segment.events import SegmentAiReceivedEvent, SegmentAiSavedEvent, SegmentErrorEvent
from application.text.segment.services.segment_crud_service import SegmentCrudService
from core.di.events import DIPublisher
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.text_data.enums import TextActionsTypes
from domain.text_data.segment.entities import SegmentTranslateEntity, SegmentVoiceEntity
from domain.text_data.segment.interfaces.repository import SegmentTranslateRepository, SegmentVoiceRepository


class SegmentAiReceivedHandler(BaseEventHandler[SegmentAiReceivedEvent, SegmentErrorEvent]):
    """
    Handles the response received from AI (e.g., translated or voiced content).
    """
    event_type = SegmentAiReceivedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentAiReceivedEvent) -> None:
        segment = await SegmentCrudService().get_by_id(event.segment_id)
        if event.action == TextActionsTypes.VOICE:
            voice_repo: SegmentVoiceRepository = DIRepository.get_repository(
                SegmentVoiceRepository,
                RepositoryTypes.TORTOISE,
            )()
            existing_voice = await voice_repo.get_by_segment(event.segment_id)
            if existing_voice is None:
                await voice_repo.save(
                    SegmentVoiceEntity(segment_id=event.segment_id, file_path=event.content)
                )
        else:
            translate_repo: SegmentTranslateRepository = DIRepository.get_repository(
                SegmentTranslateRepository,
                RepositoryTypes.TORTOISE,
            )()
            existing_translate = await translate_repo.get_by_segment(
                event.segment_id,
                segment.language_id,
                event.account_id,
            )
            if existing_translate is None:
                await translate_repo.save(
                    SegmentTranslateEntity(
                        segment_id=event.segment_id,
                        language_id=segment.language_id,
                        account_id=event.account_id,
                        translate=event.content,
                    )
                )

        await DIPublisher[SegmentAiSavedEvent, SegmentErrorEvent].publish(
            payload=SegmentAiSavedEvent(
                account_id=event.account_id,
                segment_id=event.segment_id,
                ai_log_id=event.ai_log_id,
                action=event.action,
                translate_type=event.translate_type,
                pid=event.pid,
            ),
            group_id=f"account:{event.account_id}",
        )
