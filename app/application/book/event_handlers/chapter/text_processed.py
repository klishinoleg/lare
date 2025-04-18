from application.book.datatypes.chapter_content import ChapterContentType
from application.book.services.book_crud_service import BookService
from application.book.services.chapter_crud_service import ChapterService
from application.events.event_router import register_event_handler
from application.book.services.word_chapter_saver import WordChapterSaverService
from application.book.events.chapter_events import ChapterTextProcessedEvent, ChapterWordsSavedEvent
from application.events.event_types import EventTypes
from dataclass_toolkit import deserialize_list_to_dataclass
from core.di.events import DIPublisher
from core.di.data_storage import DIDataStorage


@register_event_handler(EventTypes.CHAPTER_TEXT_PROCESSED, ChapterTextProcessedEvent)
async def handle_chapter_text_processed(event: ChapterTextProcessedEvent) -> None:
    """
    Handle text processing event: load parsed words and save into database.
    """
    data_list: list = await DIDataStorage[list].get().load_json(event.words_json_path)
    parsed_content = [deserialize_list_to_dataclass(ChapterContentType, chapter_data) for chapter_data in data_list]
    saver_service = WordChapterSaverService()
    chapter_service = ChapterService()
    book_service = BookService()
    chapter = await chapter_service.get_by_id(event.chapter_id)
    book = await book_service.get_by_id(chapter.book_id)
    await saver_service.save_words_from_chapter_content(
        chapter_id=event.chapter_id,
        language_id=book.language_id,
        content=parsed_content
    )
    await DIPublisher[ChapterWordsSavedEvent].publish(
        event_type=EventTypes.CHAPTER_WORDS_SAVED,
        payload=ChapterWordsSavedEvent(
            chapter_id=event.chapter_id,
            words_count=sum(len(ch.words) for ch in parsed_content)
        )
    )
