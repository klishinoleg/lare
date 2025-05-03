from core.enums.logger.logger_types import LoggersTypes
from infrastructure.logger.sentry import SentryLogger
from infrastructure.logger.base import BaseLogger
from core.config import settings


class DILogger:
    @staticmethod
    def get(logger_type: LoggersTypes | None = None) -> BaseLogger:
        if not logger_type:
            logger_type = settings.loggers_type
        if logger_type == LoggersTypes.SENTRY:
            return SentryLogger()
        raise ValueError(f"Logger type {logger_type} not supported.")
