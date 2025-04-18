from application.events.event_types import EventTypes
from core.enums.events.broker_types import EventBrokerTypes
from infrastructure.broker.kafka_publisher import publish_event


class DIPublisher[BE]:
    @staticmethod
    async def publish(payload: BE, event_type: EventTypes,
                      broker_type: EventBrokerTypes = EventBrokerTypes.KAFKA) -> None:
        if broker_type == EventBrokerTypes.KAFKA:
            await publish_event(payload=payload, event_type=event_type)
        else:
            raise AttributeError("Publisher {} not found".format(broker_type))
