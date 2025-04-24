from celery import Celery
from core.config import settings

celery_app = Celery(
    "lare",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_send_sent_event=True
)
