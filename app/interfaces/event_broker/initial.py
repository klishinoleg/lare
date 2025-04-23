from core.sentry import init_sentry
from core.db import init_tortoise
from core.config import settings
from tortoise_imagefield import Config


async def before_start() -> None:
    print("INTI_CONGIG")
    print("DB: {}".format(settings.database_url))
    cfg = Config()
    cfg.image_dir = settings.get_upload_dir()
    await init_tortoise()
    init_sentry()
