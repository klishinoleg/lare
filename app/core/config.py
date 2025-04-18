from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    web_app_url: str = ""
    database_url: str = ""
    secret_key: str = ""
    images_upload_dir: str = ""
    images_upload_url: str = ""
    kafka_broker_url: str = ""
    event_data_dir: str = ""

    model_config = SettingsConfigDict(env_file=Path(__file__).parent.parent / ".env", extra='ignore')

    def get_upload_dir(self) -> Path:
        path = Path(__file__).parent.parent / self.images_upload_dir
        path.mkdir(exist_ok=True)
        return path

    def get_event_data_dir(self, subdir: str, file_name: str) -> Path:
        dir_path = Path(__file__).parent.parent / self.event_data_dir / subdir
        dir_path.mkdir(exist_ok=True)
        return dir_path / file_name


# Global instance of settings to be used throughout the project
settings = Settings()
