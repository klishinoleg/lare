from application.abstract.events import BaseEventHandler
from application.book.services.chapter_crud_service import ChapterService
from application.book.events.chapter_events import ChapterWordsSavedEvent, ChapterCreationCompletedEvent, \
    ChapterCreationErrorEvent
from application.events.handler_groups import HandlerGroups
from core.di.events import DIPublisher


class ChapterWordsSavedEventHandler(BaseEventHandler[ChapterWordsSavedEvent, ChapterCreationErrorEvent]):
    event_type = ChapterWordsSavedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    @BaseEventHandler.with_error(ChapterCreationErrorEvent)
    async def handler(cls, event: ChapterWordsSavedEvent) -> None:
        """
        Handle the event when words are saved: set chapter is_ready=True and emit chapter creation completed.
        """
        chapter_service = ChapterService()
        chapter = await chapter_service.get_by_id(event.chapter_id)
        chapter.is_ready = True
        await chapter_service.update(chapter, is_system=True)
        await DIPublisher[ChapterCreationCompletedEvent, ChapterCreationErrorEvent].publish(
            payload=ChapterCreationCompletedEvent(
                pid=event.pid,
                chapter_id=chapter.id,
                book_id=chapter.book_id,
                account_id=chapter.account_id
            ),
            group_id=f"book:{chapter.book_id}"
        )
