import traceback
from typing import Type

from application.abstract.events import BaseEvent
from application.events.event_types import EventTypes
from core.enums.events.broker_types import EventBrokerTypes
from infrastructure.broker.celery.broker import CeleryEventBroker
from infrastructure.broker.celery.publisher import CeleryPublisher
from infrastructure.broker.kafka.publisher import KafkaPublisher
from infrastructure.broker.base_broker import BaseBroker
from infrastructure.broker.kafka.broker import KafkaEventBroker
from core.config import settings


class DIPublisher[BE: BaseEvent, ET: EventTypes]:
    @staticmethod
    async def publish(payload: BE,
                      group_id: str | None = None,
                      broker_type: EventBrokerTypes | None = None) -> None:
        if broker_type is None:
            broker_type = settings.event_broker_type
        publisher = None
        if broker_type == EventBrokerTypes.KAFKA:
            publisher = KafkaPublisher()
        elif broker_type == EventBrokerTypes.CELERY:
            publisher = CeleryPublisher()
        if not publisher:
            raise AttributeError("Publisher {} not found".format(broker_type))
        await publisher.publish(payload=payload, group_id=group_id)

    @classmethod
    async def publish_error(
            cls, event_error_model: Type[BE], ex: Exception, step: ET, group_id: str, **kwargs: dict
    ) -> None:
        await cls.publish(
            payload=event_error_model(
                error_message=str(ex),
                traceback=traceback.format_exc(),
                step=step,
                **kwargs
            ),
            group_id=group_id
        )


class DIBrokerManager[BS: BaseBroker]:
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
        else:
            raise AttributeError("Broker {} not found".format(broker_type))
