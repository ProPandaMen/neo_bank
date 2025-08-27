from database.models.task import TaskLogs

import json


def add_log(task_id: int, source: str, stage: str, message: str):
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
