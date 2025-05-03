from application.abstract.events import BaseEventHandler
from application.book.datatypes.chapter_content import ChapterContentWordType
from application.book.services.book_crud_service import BookService
from application.book.services.chapter_crud_service import ChapterService
from application.book.services.word_chapter_saver import WordChapterSaverService
from application.book.events.chapter_events import ChapterTextProcessedEvent, ChapterWordsSavedEvent, \
    ChapterCreationErrorEvent
from dataclass_toolkit import deserialize_list_to_dataclass

from application.events.handler_groups import HandlerGroups
from core.di.events import DIPublisher


class ChapterTextProcessedEventHandler(BaseEventHandler[ChapterTextProcessedEvent, ChapterCreationErrorEvent]):
    event_type = ChapterTextProcessedEvent.event_type
    event_handler_group: HandlerGroups = HandlerGroups.CHAPTER

    @classmethod
    @BaseEventHandler.with_error(ChapterCreationErrorEvent)
    async def handler(cls, event: ChapterTextProcessedEvent) -> None:
        """
        Handle text processing event: load parsed words and save into database.
        """
        parsed_content = [deserialize_list_to_dataclass(ChapterContentWordType, chapter_data) for chapter_data in
                          event.words_data]
        saver_service = WordChapterSaverService()
        chapter_service = ChapterService()
        book_service = BookService()
        chapter = await chapter_service.get_by_id(event.chapter_id)
        book = await book_service.get_by_id(chapter.book_id)
        await saver_service.save_words_from_chapter_content(
            chapter=chapter,
            content=parsed_content
        )
        await DIPublisher[ChapterWordsSavedEvent, ChapterCreationErrorEvent].publish(
            payload=ChapterWordsSavedEvent(
                pid=event.pid,
                chapter_id=event.chapter_id,
                words_count=len(parsed_content)
            ),
            group_id=f"book:{book.id}",
        )
