from typing import TYPE_CHECKING
from infrastructure.broker.base_publisher import BasePublisher
from infrastructure.broker.celery.app import celery_app

if TYPE_CHECKING:
    from application.abstract.events import BaseEvent


class CeleryPublisher[BE: "BaseEvent"](BasePublisher):
    @classmethod
    async def publish(cls, payload: BE, group_id: str | None) -> None:
        data = payload.model_dump()
        if group_id:
            data["group_id"] = group_id
        celery_app.send_task(payload.event_type.value, kwargs=data)
