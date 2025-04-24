from application.abstract.events import BaseEventHandler
from application.book.services.chapter_crud_service import ChapterService
from application.book.utils.text_processing import process_text_to_chapters
from application.book.events.chapter_events import ChapterCreateRequestedEvent, ChapterTextProcessedEvent, \
    ChapterCreationErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.events import DIPublisher
from dataclass_toolkit import serialize_dataclass_to_list


class ChapterCreateRequestedEventHandler[BE: ChapterCreateRequestedEvent](BaseEventHandler[BE]):
    event_type = ChapterCreateRequestedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    async def handler(cls, event: ChapterCreateRequestedEvent, group_id: int | None) -> None:
        """
        Handle the creation of a chapter after receiving the requested event.
        """
        try:
            chaper_sevice = ChapterService()
            created_chapter = await chaper_sevice.get_by_id(id=event.chapter_id)
            words = await process_text_to_chapters(event.text)
            await DIPublisher[ChapterCreateRequestedEvent].publish(
                payload=ChapterTextProcessedEvent(
                    chapter_id=created_chapter.id,
                    words_data=[serialize_dataclass_to_list(word) for word in words],
                ),
                group_id=f"book:{event.book_id}",
            )
        except Exception as ex:
            await DIPublisher[ChapterCreationErrorEvent].publish_error(
                event_error_model=ChapterCreationErrorEvent,
                ex=ex,
                step=event.event_type,
                group_id=f"book:{event.book_id}",
                book_id=event.book_id,
                chapter_id=event.chapter_id,
            )
