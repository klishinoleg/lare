from application.book.event_handlers.chapter import (
    ChapterCreateRequestedEventHandler,
    ChapterCreationComplitedEventHandler,
    ChapterCreationErrorEventHandler,
    ChapterTextProcessedEventHandler,
    ChapterWordsSavedEventHandler,
)
from application.book.events.chapter_events import (
    ChapterCreateRequestedEvent,
    ChapterCreationCompletedEvent,
    ChapterCreationErrorEvent,
    ChapterTextProcessedEvent,
    ChapterWordsSavedEvent,
)
from core.di.events import DIBrokerManager
from core.enums.events.broker_types import EventBrokerTypes


def register_chapter_brokers(broker_type: EventBrokerTypes | None = None) -> None:
    broker = DIBrokerManager.get(broker_type)
    broker.subscribe(ChapterCreateRequestedEventHandler, ChapterCreateRequestedEvent)
    broker.subscribe(ChapterTextProcessedEventHandler, ChapterTextProcessedEvent)
    broker.subscribe(ChapterWordsSavedEventHandler, ChapterWordsSavedEvent)
    broker.subscribe(ChapterCreationComplitedEventHandler, ChapterCreationCompletedEvent)
    broker.subscribe(ChapterCreationErrorEventHandler, ChapterCreationErrorEvent)
