from typing import TYPE_CHECKING
from core.config import settings
from faststream.kafka import KafkaBroker
from infrastructure.broker.base_publisher import BasePublisher

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent

broker = KafkaBroker(settings.kafka_bootstrap_servers)


class KafkaPublisher[BE: "BaseEvent"](BasePublisher):
    @classmethod
    async def publish(cls, payload: "BE", group_id: str | None) -> None:
        """
        Publishes an event to Kafka.

        Args:
            event_type (ChapterEventTypes): The type of event (topic name).
            payload (dict): The event data (serialized).
            :param payload:
            :param group_id:
        """

        async def publ() -> None:
            await broker.publish(
                payload.model_dump(),
                topic=payload.event_type.value,
                key=str(group_id).encode('utf-8') if group_id is not None else None
            )

        try:
            await publ()
        except AssertionError:
            await broker.connect()
            await publ()

    @classmethod
    async def on_start(cls) -> None:
        await broker.connect()

    @classmethod
    async def on_stop(cls) -> None:
        await broker.close()
