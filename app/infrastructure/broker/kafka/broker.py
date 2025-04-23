from typing import Type, Callable, Awaitable
from faststream import Context, FastStream
from application.abstract.events import BaseEvent, BaseEventHandler
from core.config import settings
from faststream.kafka import KafkaBroker
from infrastructure.broker.base_broker import BaseBroker


class KafkaEventBroker[BEH: BaseEventHandler, BE: BaseEvent](BaseBroker):
    """
    Kafka implementation of event subscriber.
    """

    def __init__(self) -> None:
        super().__init__()
        self.broker = KafkaBroker(
            settings.kafka_bootstrap_servers
        )
        self.app = FastStream(self.broker)

    def subscribe(self, handler: Type[BEH], event_model: Type[BE]) -> None:
        @self.broker.subscriber(
            handler.event_type.value,
            group_id=handler.event_handler_group, auto_commit=False
        )
        async def kafka_handler(data: event_model,  # type:ignore[valid-type, no-untyped-def]
                                message=Context()) -> None:
            await message.ack()
            await handler.execute(data)

    async def _start_broker(self) -> None:
        await self.app.run()

    def before_start(self, func: Callable[[], Awaitable]) -> None:
        self.app.on_startup(func)
