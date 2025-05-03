from application.book.events.chapter_events import ChapterTextProcessedEvent, ChapterCreateRequestedEvent, \
    ChapterWordsSavedEvent, ChapterCreationCompletedEvent, ChapterCreationErrorEvent
from core.di.events import DIBrokerManager
from application.book.event_handlers.chapter import ChapterTextProcessedEventHandler, ChapterWordsSavedEventHandler, \
    ChapterCreationComplitedEventHandler, ChapterCreateRequestedEventHandler, ChapterCreationErrorEventHandler
from core.enums.events.broker_types import EventBrokerTypes
from interfaces.event_broker.initial import before_start

broker = DIBrokerManager.get(EventBrokerTypes.KAFKA)

broker.before_start(before_start)
broker.subscribe(ChapterCreateRequestedEventHandler, ChapterCreateRequestedEvent)
broker.subscribe(ChapterTextProcessedEventHandler, ChapterTextProcessedEvent)
broker.subscribe(ChapterWordsSavedEventHandler, ChapterWordsSavedEvent)
broker.subscribe(ChapterCreationComplitedEventHandler, ChapterCreationCompletedEvent)
broker.subscribe(ChapterCreationErrorEventHandler, ChapterCreationErrorEvent)
app = broker.app


if __name__ == "__main__":
    broker.run()
