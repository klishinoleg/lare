import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.db import init_tortoise, close_tortoise
from core.di.events import DIPublisher
from core.enums.events.broker_types import EventBrokerTypes
from core.sentry import init_sentry
from core.registrators.init_auth_providers import register_auth_providers
from application.events.handlers_register.chapter import register_chapter_brokers
from application.events.handlers_register.finance import register_finance_main_brokers
from application.events.handlers_register.segment import register_segment_brokers
from interfaces.fast_api.routers import (
    auth_router,
    book_router,
    compat_router,
    health_router,
    language_router,
    transaction_router,
)
from interfaces.fast_api.exceptions.custom import register_exception_handler
from core.config import settings
from infrastructure.ai.provider_bootstrap import configure_reader_ai_provider
from tortoise_imagefield import Config

app = FastAPI()
cfg = Config()
cfg.image_dir = settings.get_upload_dir()
os.makedirs(settings.get_upload_dir(), exist_ok=True)
upload_url = settings.images_upload_url or "uploads"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
async def startup() -> None:
    configure_reader_ai_provider()
    await init_tortoise()
    init_sentry()
    if settings.event_broker_type == EventBrokerTypes.MOCK:
        register_chapter_brokers(EventBrokerTypes.MOCK)
        register_finance_main_brokers(EventBrokerTypes.MOCK)
        register_segment_brokers(EventBrokerTypes.MOCK)
    await DIPublisher.start()


async def shutdown() -> None:
    await close_tortoise()
    await DIPublisher.stop()


app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

register_exception_handler(app)
register_auth_providers()
app.mount(f"/{upload_url}", StaticFiles(directory=settings.get_upload_dir()), name="uploads")
app.include_router(book_router)
app.include_router(auth_router)
app.include_router(language_router)
app.include_router(transaction_router)
app.include_router(compat_router)
app.include_router(health_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
