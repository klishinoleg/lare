from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from aiofiles import os
from core.enums.bot.bot_types import BotTypes
from core.enums.dev.enviroment_types import EnviromentTypes
from core.enums.events.broker_types import EventBrokerTypes
from core.enums.events.streaming import EventStreamingTypes
from core.enums.logger.logger_types import LoggersTypes
from core.enums.repository.types import RepositoryTypes
from core.enums.storage.deduplicator import DeduplicatorTypes


class Settings(BaseSettings):
    """
    Application-wide configuration settings loaded from environment variables.

    This class defines key configuration options required throughout the project,
    such as language defaults, database connections, and third-party API tokens.

    Environment variables are loaded automatically from a `.env` file in the project root.

    Attributes:
        default_language (str): Default language code used in the application.
        tg_bot_token (str): Telegram bot token used for validating initData.
        web_app_url (str): Publicly accessible URL of the web application.
        database_url (str): URL for connecting to the application's database.
    """

    default_language: str = "en"
    tg_bot_token: str = ""
    tg_payment_provider_token: str = ""
    telegram_admin_user_ids: str = ""
    web_app_url: str = ""
    database_url: str = ""
    slave_database_url: str | None = None
    redis_url: str = ""
    redis_event_streaming_url: str = ""
    secret_key: str = ""
    images_upload_dir: str = ""
    images_upload_url: str = ""
    kafka_broker_url: str = ""
    kafka_bootstrap_servers: str = ""
    event_data_dir: str = ""
    celery_app_name: str = "lare"
    celery_broker_url: str = ""
    celery_backend_url: str = ""
    sentry_redis_url: str = ""
    sentry_secret_key: str = ""
    sentry_dsn: str = ""
    credits_start_bonus: int = 100
    event_streaming_timeout: float = 15
    event_outbox_max_attempts: int = 3
    reader_ai_provider: str = "local"
    reader_ai_openai_api_key: str = ""
    reader_ai_openai_base_url: str = "https://api.openai.com/v1"
    reader_ai_openai_chat_model: str = "gpt-4o-mini"
    reader_ai_openai_image_model: str = "dall-e-3"
    reader_ai_openai_speech_model: str = "tts-1"
    reader_ai_openai_speech_voice: str = "alloy"
    reader_ai_openai_image_size: str = "1024x1024"
    reader_ai_voice_provider: str = ""
    reader_ai_google_tts_language_code: str = "en-US"
    reader_ai_google_tts_gender: str = "MALE"
    google_application_credentials: str = ""
    enviroment: EnviromentTypes = EnviromentTypes.PRODUCTION
    default_bot: BotTypes = BotTypes.TELEGRAM
    default_event_streaming: EventStreamingTypes = EventStreamingTypes.REDIS
    loggers_type: LoggersTypes = LoggersTypes.SENTRY
    event_broker_type: EventBrokerTypes = EventBrokerTypes.KAFKA
    deduplicator_type: DeduplicatorTypes = DeduplicatorTypes.REDIS
    repository_type: RepositoryTypes = RepositoryTypes.TORTOISE
    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env", extra='ignore')
    languages: str = ""
    language_code: str = "en"
    locales_dir: str = "locales"

    def get_languages(self) -> tuple[tuple[str, str], ...]:
        return tuple(lang for lang in (
            ("en", "English"),
            ("zh", "中文"),
            ("es", "Español"),
            ("ar", "العربية"),
            ("hi", "हिंदी"),
            ("fr", "Français"),
            ("ru", "Русский"),
            ("pt", "Português"),
            ("bn", "বাংলা"),
            ("de", "Deutsch"),
            ("ja", "日本語"),
            ("ko", "한국어"),
            ("it", "Italiano"),
            ("tr", "Türkçe"),
            ("nl", "Nederlands"),
        ) if lang[0] in self.languages.split("|"))

    def get_upload_dir(self) -> Path:
        path = Path(__file__).parent.parent / self.images_upload_dir
        path.mkdir(exist_ok=True)
        return path

    def get_locales_dir(self) -> Path:
        path = Path(__file__).parent / self.locales_dir
        path.mkdir(exist_ok=True)
        return path

    async def get_event_data_dir(self, subdir: str, file_name: str) -> Path:
        dir_path = Path(__file__).parent.parent / self.event_data_dir / subdir
        if not await os.path.exists(dir_path):
            await os.makedirs(dir_path, exist_ok=True)
        return dir_path / file_name


# Global instance of settings to be used throughout the project
settings = Settings()
