from logging.config import dictConfig
from config import LOG_FILE

import logging


_old = logging.getLogRecordFactory()

def _factory(*args, **kwargs):
    r = _old(*args, **kwargs)
    if not hasattr(r, "task_name"): r.task_name = ""
    if not hasattr(r, "task_id"): r.task_id = ""
    return r

logging.setLogRecordFactory(_factory)


dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","pid":%(process)d,"task":"%(task_name)s","task_id":"%(task_id)s","msg":"%(message)s","exc":"%(exc_text)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/app/logs/celery.log",
            "maxBytes": 10000000,
            "backupCount": 5,
            "formatter": "json",
            "encoding": "utf-8"
        },
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        }
    },
    "root": {"handlers": ["file", "stdout"], "level": "INFO"}
})
