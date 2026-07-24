from application.abstract.events import BaseEventHandler
from application.book.services.word_chapter_saver import WordChapterSaverService
from application.events.handler_groups import HandlerGroups
from application.text.segment.services.segment_crud_service import SegmentCrudService
from application.text.segment.events import (
    SegmentCreateRequestedEvent, SegmentCreatedEvent,
    SegmentErrorEvent
)
from core.di.events import DIPublisher
from core.di.repository import DIRepository
from core.enums.repository.types import RepositoryTypes
from domain.text.segment.entities import SegmentEntity
from domain.text.segment.interfaces.repository import SegmentRepository
from domain.text.word.interfaces.repository import WordRepository


class SegmentCreateRequestedHandler(BaseEventHandler[SegmentCreateRequestedEvent, SegmentErrorEvent]):
    """
    Handles the initial request to create a segment from word chapter indexes.
    """
    event_type = SegmentCreateRequestedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.SEGMENT

    @classmethod
    @BaseEventHandler.with_error(SegmentErrorEvent)
    async def handler(cls, event: SegmentCreateRequestedEvent) -> None:
        word_chapter_service = WordChapterSaverService()
        word_chapters = [
            await word_chapter_service.get_by_id(word_chapter_id)
            for word_chapter_id in event.dto.indexes
        ]
        word_chapters = sorted(word_chapters, key=lambda item: item.position)
        chapter_ids = {item.chapter_id for item in word_chapters}
        if len(chapter_ids) != 1:
            raise ValueError("Segment selection must belong to one chapter.")

        word_repo = DIRepository.get_repository(WordRepository, RepositoryTypes.TORTOISE)()
        first_word = await word_repo.get_by_id(word_chapters[0].word_id)
        if first_word is None:
            raise ValueError("Segment source word was not found.")

        segment_name = " ".join(item.name for item in word_chapters).strip()
        if not segment_name:
            raise ValueError("Segment text is empty.")

        segment_repo: SegmentRepository = DIRepository.get_repository(
            SegmentRepository,
            RepositoryTypes.TORTOISE,
        )()
        segment = await segment_repo.get_by_name_and_language(segment_name, first_word.language_id)
        if segment is None:
            segment = await SegmentCrudService().create(
                SegmentEntity(name=segment_name, language_id=first_word.language_id)
            )

        for word_chapter in word_chapters:
            if word_chapter.segment_id != segment.id:
                await word_chapter_service.update_segment(word_chapter.id, segment.id)

        await DIPublisher[SegmentCreatedEvent, SegmentErrorEvent].publish(
            payload=SegmentCreatedEvent(
                account_id=event.account_id,
                segment_id=segment.id,
                ai_model=event.ai_model,
                action=event.dto.a,
                translate_type=event.dto.translate_type,
                pid=event.pid,
            ),
            group_id=f"account:{event.account_id}",
        )
