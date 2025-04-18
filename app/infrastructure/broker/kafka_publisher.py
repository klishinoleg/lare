from core.config import settings
from faststream.kafka import KafkaBroker
from application.events.event_types import EventTypes
from application.abstract.events import BaseEvent

broker = KafkaBroker(settings.kafka_broker_url)


async def publish_event(event_type: EventTypes, payload: BaseEvent) -> None:
    """
    Publishes an event to Kafka.

    Args:
        event_type (EventTypes): The type of event (topic name).
        payload (dict): The event data (serialized).
    """
    await broker.publish(
        payload,
        topic=event_type.value,
    )
