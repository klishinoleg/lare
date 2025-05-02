import sentry_sdk
from infrastructure.logger.base import BaseLogger
from application.abstract.events import BaseErrorEvent


class SentryLogger(BaseLogger):
    async def _event_log(self, event: BaseErrorEvent) -> None:
        scope = sentry_sdk.Scope()
        for field, value in event.model_dump().items():
            scope.set_context(field, {"value": value})
        sentry_sdk.capture_message(
            f"Logged event: {event.__class__.__name__}",
            scope=scope
        )
