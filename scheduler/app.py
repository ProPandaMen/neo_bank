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
    task_routes={
        "scheduler.tick": {"queue": "scheduler"},
        "scheduler.retry_tick": {"queue": "scheduler"},
        "scheduler.execute_pipeline": {"queue": "executor"},
    },
    beat_schedule={
        "tick": {"task": "scheduler.tick", "schedule": 5.0},
        "retry-tick": {"task": "scheduler.retry_tick", "schedule": 10.0},
    },
)

