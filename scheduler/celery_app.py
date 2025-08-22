from celery import Celery
from config import CELERY_BROKER_URL, CELERY_BACKEND_URL


celery_app = Celery(
    "neo_bank",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    include=["scheduler.tasks"],
    task_routes={
        "scheduler.scheduler_tick": {"queue": "scheduler"},
        "scheduler.pipeline_execute": {"queue": "scheduler"},
        "scheduler.scheduler_retry": {"queue": "executor"},
    },
    beat_schedule={
        "scheduler_tick": {"task": "scheduler.scheduler_tick", "schedule": 5.0},
        "scheduler_retry": {"task": "scheduler.scheduler_retry", "schedule": 10.0},
    },
)
