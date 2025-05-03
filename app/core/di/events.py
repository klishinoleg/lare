import traceback
from typing import Type, TYPE_CHECKING
from application.events.event_types import EventTypes
from application.events.streaming.types import StreamingTypes
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from infrastructure.broker.base_publisher import BasePublisher
from infrastructure.broker.celery.broker import CeleryEventBroker
from infrastructure.broker.celery.publisher import CeleryPublisher
from infrastructure.broker.kafka.publisher import KafkaPublisher
from infrastructure.broker.kafka.broker import KafkaEventBroker
from core.config import settings
from infrastructure.broker.mock.broker import MockEventBroker
from infrastructure.broker.mock.publisher import MockPublisher
from infrastructure.event_streaming.mock_streaming import MockEventStreaming
from infrastructure.event_streaming.redis_streaming import RedisEventStreaming

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent, BaseErrorEvent
    from infrastructure.event_streaming.base import BaseEventStreaming
    from infrastructure.broker.base_broker import BaseBroker


class DIPublisher[BE: "BaseEvent", BER: "BaseErrorEvent"]:

    @classmethod
    def get_broker(cls, broker_type: EventBrokerTypes | None = None) -> BasePublisher:
        if broker_type is None:
            broker_type = settings.event_broker_type
        if broker_type == EventBrokerTypes.KAFKA:
            return KafkaPublisher()
        if broker_type == EventBrokerTypes.CELERY:
            return CeleryPublisher()
        if broker_type == EventBrokerTypes.MOCK:
            return MockPublisher()
        raise AttributeError("Publisher {} not found".format(broker_type))

    @classmethod
    async def publish(cls, payload: BE,
                      group_id: str | None = None,
                      broker_type: EventBrokerTypes | None = None) -> None:
        await cls.get_broker(broker_type).publish(payload=payload, group_id=group_id)

    @classmethod
    async def start(cls, broker_type: EventBrokerTypes | None = None) -> None:
        await cls.get_broker(broker_type).on_start()

    @classmethod
    async def stop(cls, broker_type: EventBrokerTypes | None = None) -> None:
        await cls.get_broker(broker_type).on_stop()

    @classmethod
    async def publish_error(
            cls, event_error_model: Type[BER], ex: Exception, step: EventTypes, is_expected: bool = False,
            **kwargs: dict
    ) -> None:
        await cls.publish(
            payload=event_error_model(
                error_message=str(ex),
                traceback=None if is_expected else traceback.format_exc(),
                is_expected=bool(is_expected),
                step=step,
                **kwargs
            ),
        )


class DIBrokerManager[BS: "BaseBroker"]:
    """
    Dependency injector for selecting the event subscriber implementation.
    """

    @staticmethod
    def get(broker_type: EventBrokerTypes | None = None) -> BS:
        if broker_type is None:
            broker_type = settings.event_broker_type
        if broker_type == EventBrokerTypes.KAFKA:
            return KafkaEventBroker()
        elif broker_type == EventBrokerTypes.CELERY:
            return CeleryEventBroker()
        elif broker_type == EventBrokerTypes.MOCK:
            return MockEventBroker()
        else:
            raise AttributeError("Broker {} not found".format(broker_type))


class DIEventStreaming:
    @classmethod
    def get(cls, *args: tuple,
            streaming_type: StreamingTypes | None = None,
            event_streaming: EventStreamingTypes | None = None,
            pid: str | None = None) -> "BaseEventStreaming":
        if not event_streaming:
            event_streaming = settings.default_event_streaming
        if event_streaming == EventStreamingTypes.REDIS:
            return RedisEventStreaming(*args, streaming_type=streaming_type, pid=pid)
        if event_streaming == EventStreamingTypes.MOCK:
            return MockEventStreaming(*args, streaming_type=streaming_type, pid=pid)
        raise AttributeError("Event streaming service {} not found".format(event_streaming))
