from sentry_sdk import Hub
from infrastructure.logger.base import BaseLogger
from application.abstract.events import BaseErrorEvent


class SentryLogger(BaseLogger):
    async def event_log(self, event: BaseErrorEvent) -> None:
        hub = Hub.current
        with hub.push_scope() as scope:
            for field, value in event.model_dump().items():
                scope.set_extra(field, value)
            hub.capture_message(f"Logged event: {event.__class__.__name__}")
