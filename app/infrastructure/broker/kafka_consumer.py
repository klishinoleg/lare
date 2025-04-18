from core.config import settings
from faststream.kafka import KafkaBroker
from application.events.event_types import EventTypes
from application.events.event_router import event_handlers
broker = KafkaBroker(settings.kafka_broker_url)


def get_event_type_by_topic(topic: str) -> EventTypes:
    for event_type in EventTypes:
        if event_type.value == topic:
            return event_type
    raise ValueError(f"Unknown topic: {topic}")


@broker.subscriber("#")  # Subscribe to all topics
async def universal_event_handler(event_data: dict, topic: str) -> None:
    event_type = get_event_type_by_topic(topic)
    handler_entry = event_handlers.get(event_type)

    if not handler_entry:
        # No handler registered for this event, silently ignore or log
        return

    event_model_class, handler = handler_entry

    try:
        # Validate and parse event
        event_object = event_model_class.model_validate(event_data)

        # Call the correct handler with parsed event
        await handler(event_object)

    except Exception as e:
        # Optional: Add error logging here
        raise e
