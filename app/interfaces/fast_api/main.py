import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.db import init_tortoise, close_tortoise
from core.sentry import init_sentry
from infrastructure.auth.init_auth_providers import register_auth_providers
from interfaces.fast_api.routers import book_router, auth_router, language_router
from interfaces.fast_api.exceptions.custom import register_exception_handler
from core.config import settings
from tortoise_imagefield import Config

app = FastAPI()
cfg = Config()
cfg.image_dir = settings.get_upload_dir()
os.makedirs(settings.get_upload_dir(), exist_ok=True)


async def startup() -> None:
    await init_tortoise()
    init_sentry()


async def shutdown() -> None:
    await close_tortoise()


app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

register_exception_handler(app)
register_auth_providers()
app.mount(f"/{settings.images_upload_url}", StaticFiles(directory=settings.get_upload_dir()), name="uploads")
app.include_router(book_router)
app.include_router(auth_router)
app.include_router(language_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
