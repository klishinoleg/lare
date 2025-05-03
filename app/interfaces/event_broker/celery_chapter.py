from application.book.events.chapter_events import ChapterWordsSavedEvent, ChapterCreateRequestedEvent, \
    ChapterCreationErrorEvent, ChapterTextProcessedEvent, ChapterCreationCompletedEvent
from core.di.events import DIBrokerManager
from application.book.event_handlers.chapter import ChapterTextProcessedEventHandler, ChapterWordsSavedEventHandler, \
    ChapterCreationComplitedEventHandler, ChapterCreateRequestedEventHandler, ChapterCreationErrorEventHandler
from core.enums.events.broker_types import EventBrokerTypes
from core.config import settings
from interfaces.event_broker.initial import before_start

settings.event_broker_type = EventBrokerTypes.CELERY

broker = DIBrokerManager.get(EventBrokerTypes.CELERY)

broker.before_start(before_start)
broker.subscribe(ChapterTextProcessedEventHandler, ChapterTextProcessedEvent)
broker.subscribe(ChapterWordsSavedEventHandler, ChapterWordsSavedEvent)
broker.subscribe(ChapterCreationComplitedEventHandler, ChapterCreationCompletedEvent)
broker.subscribe(ChapterCreateRequestedEventHandler, ChapterCreateRequestedEvent)
broker.subscribe(ChapterCreationErrorEventHandler, ChapterCreationErrorEvent)
broker.run()

if __name__ == '__main__':
    pass
