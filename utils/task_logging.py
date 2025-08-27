from database.models.task import TaskLogs

import json
import os


TASKLOG_MAX = int(os.getenv("TASKLOG_MAX", "4000"))


def add_log(task_id: int, source: str, stage: str, message: str):
    msg = str(message or "")
    truncated = len(msg) > TASKLOG_MAX

    if truncated:
        cut = msg[:TASKLOG_MAX]
        cut += f" … [обрезано {len(msg)-TASKLOG_MAX} симв.]"
        msg = cut

    TaskLogs.create(task_id=task_id, description=json.dumps({
        "source": source,
        "stage": stage,
        "message": message
    }, ensure_ascii=False))


def log_task(task_id: int, stage: str, message: str):
    add_log(task_id, "task", stage, message)


def log_celery(task_id: int, stage: str, message: str):
    add_log(task_id, "celery", stage, message)


def log_dashboard(task_id: int, stage: str, message: str):
    add_log(task_id, "dashboard", stage, message)
