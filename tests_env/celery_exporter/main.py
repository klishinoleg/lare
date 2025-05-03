import asyncio
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response
from celery import Celery
from celery.events import EventReceiver
from celery.app.control import Inspect
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

celery_app = Celery(
    broker=os.environ.get("CELERY_BROKER_URL")
)

task_started_total = Counter('celery_task_started_total', 'Total tasks started')
task_succeeded_total = Counter('celery_task_succeeded_total', 'Total tasks succeeded')
task_failed_total = Counter('celery_task_failed_total', 'Total tasks failed')
active_workers_gauge = Gauge('celery_worker_up', 'Number of active celery workers')


async def listen_for_events() -> None:
    def _capture_events() -> None:
        with celery_app.connection() as connection:
            recv = EventReceiver(
                connection,
                handlers={
                    'task-started': lambda event: task_started_total.inc(),
                    'task-succeeded': lambda event: task_succeeded_total.inc(),
                    'task-failed': lambda event: task_failed_total.inc(),
                },
                app=celery_app,
            )
            recv.capture(limit=None, timeout=None, wakeup=True)

    await asyncio.to_thread(_capture_events)


async def startup_event() -> None:
    loop = asyncio.get_event_loop()
    loop.create_task(listen_for_events())


app.add_event_handler("startup", startup_event)


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/check_workers")
async def check_workers() -> dict:
    try:
        i = Inspect(app=celery_app)
        stats = i.stats()
        active_workers_gauge.set(len(stats.keys()) if stats else 0)
    except Exception as e:
        print(e)
        active_workers_gauge.set(0)
    return {"workers": active_workers_gauge._value.get()}
