import asyncio
from typing import Type, TYPE_CHECKING
from infrastructure.broker.base_broker import BaseBroker
from infrastructure.broker.celery.app import celery_app
from celery.worker.worker import WorkController

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent, BaseEventHandler


class CeleryEventBroker(BaseBroker):

    def __init__(self) -> None:
        self.app = celery_app
        super().__init__()

    def subscribe[BEH: "BaseEventHandler", BE: "BaseEvent"](self, handler: Type[BEH], event_model: Type[BE]) -> None:
        q_name = handler.event_type.value.split(".")[0]

        @self.app.task(name=handler.event_type.value, queue=q_name)
        def handle_event(**kwargs: dict) -> None:
            payload = event_model.model_validate(kwargs)
            asyncio.run(handler.execute(event=payload))

    async def _start_broker(self) -> None:
        celery_worker_instance = WorkController(app=self.app, pool="solo")
        celery_worker_instance.start()
