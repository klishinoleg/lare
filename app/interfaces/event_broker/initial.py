from fastapi18n import TranslationWrapper

from core.sentry import init_sentry
from core.db import init_tortoise
from core.config import settings
from tortoise_imagefield import Config


async def before_start() -> None:
    cfg = Config()
    cfg.image_dir = settings.get_upload_dir()
    await init_tortoise()
    init_sentry()
    TranslationWrapper.init(locales_dir=settings.get_locales_dir(),
                            languages=settings.get_languages(),
                            language=settings.language_code)
