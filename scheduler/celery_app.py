from celery import Celery
from kombu import Queue
from config import CELERY_BROKER_URL, CELERY_BACKEND_URL


celery_app = Celery(
    "neo_bank",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)

celery_app.conf.update(
    task_queues=(Queue("scheduler"), Queue("executor")),
    task_default_queue="scheduler",
    include=["scheduler.planner", "scheduler.task_runner"],
    task_routes={
        "scheduler.planner": {"queue": "scheduler"},
        "scheduler.task_execute": {"queue": "executor"},
    },
    beat_schedule={
        "planner-tick": {
            "task": "scheduler.planner",
            "schedule": 10.0,
        },
    },
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_transport_options={"visibility_timeout": 7200},
)
