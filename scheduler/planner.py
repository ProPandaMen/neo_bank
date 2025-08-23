from celery.utils.log import get_task_logger
from sqlalchemy import and_
from .celery_app import celery_app
from database.models.task import Task, TaskLogs, StepStatus, TaskSettings


logger = get_task_logger("planner")


def _settings():
    ts = TaskSettings.get(name="default")

    if not ts:
        ts = TaskSettings.create(name="default", scripts=[])

    parallel_limit = getattr(ts, "parallel_limit", 1) or 1
    create_batch = getattr(ts, "create_batch", 1) or 1
    scripts = list(ts.scripts or [])
    
    return scripts, int(parallel_limit), int(create_batch)


@celery_app.task(name="scheduler.planner")
def planer():
    scripts, parallel_limit, create_batch = _settings()
    running = Task.filter(step_status=StepStatus.RUNNING)
    capacity = max(0, parallel_limit - len(running))
    started = 0
    retried = 0
    created = 0

    if capacity > 0:
        ready = Task.filter_ex(where=[and_(Task.step_index < Task.steps_total, Task.step_status == StepStatus.WAITING)], order_by=Task.created_at.asc(), limit=capacity)
        for t in ready:
            celery_app.send_task("scheduler.task_execute", args=[t.id], queue="executor")
            started += 1
        capacity -= started

    if capacity > 0:
        failed = Task.filter(step_status=StepStatus.ERROR, order_by=Task.created_at.asc(), limit=capacity)
        for t in failed:
            celery_app.send_task("scheduler.task_execute", args=[t.id], queue="executor")
            retried += 1
        capacity -= retried

    if capacity > 0 and scripts:
        n = min(create_batch, capacity)
        for _ in range(n):
            t = Task.create(step_index=0, steps_total=len(scripts), step_status=StepStatus.WAITING)
            TaskLogs.create(task_id=t.id, description="created by planner")
            created += 1

    logger.info(f"started={started} retried={retried} created={created} cap={parallel_limit}")
    return {"started": started, "retried": retried, "created": created, "parallel_limit": parallel_limit}
