import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

from core.config import settings  # путь к твоему settings
from core.enums.dev.enviroment_types import EnviromentTypes


def init_sentry() -> None:
    """
    Initialize Sentry depending on environment.
    """
    if not settings.sentry_dsn:
        return

    integrations = [
        LoggingIntegration(),
        AsyncioIntegration(),
    ]

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=integrations,
        environment=settings.enviroment,
        traces_sample_rate=1.0 if settings.enviroment == EnviromentTypes.PRODUCTION else 0.0,
        send_default_pii=True,
        default_integrations=False
    )
