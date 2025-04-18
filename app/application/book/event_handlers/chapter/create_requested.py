from application.events.event_router import register_event_handler
from application.book.services.text_processing import process_text_to_chapters
from application.book.events.chapter_events import ChapterCreateRequestedEvent, ChapterTextProcessedEvent
from application.events.event_types import EventTypes
from core.config import settings
from core.di.data_storage import DIDataStorage
from core.di.events import DIPublisher
from dataclass_toolkit import serialize_dataclass_to_list


@register_event_handler(EventTypes.CHAPTER_CREATE_REQUESTED, ChapterCreateRequestedEvent)
async def handle_chapter_create_requested(event: ChapterCreateRequestedEvent) -> None:
    """
    Handle the creation of a chapter after receiving the requested event.
    """
    chapters = await process_text_to_chapters(event.text)
    save_path = settings.get_event_data_dir("chapters", f"{event.book_id}_{event.name}.json")
    await DIDataStorage[list].get().save_json(save_path, [serialize_dataclass_to_list(chapter) for chapter in chapters])
    await DIPublisher[ChapterCreateRequestedEvent].publish(
        event_type=EventTypes.CHAPTER_TEXT_PROCESSED,
        payload=ChapterTextProcessedEvent(
            chapter_id=event.book_id,
            words_json_path=save_path,
        ),
    )
