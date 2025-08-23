from celery.utils.log import get_task_logger
from scheduler.celery_app import celery_app

from database.models.task import Task, TaskLogs, StepStatus, TaskSettings

import subprocess
import sys


logger = get_task_logger("task_runner")


def run_script(path: str, task_id: int):
    cmd = [sys.executable, path, str(task_id)] if path.endswith(".py") else [path, str(task_id)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


@celery_app.task(name="scheduler.task_execute")
def task_execute(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        logger.error(f"Task {task_id} not found")
        return "missing"

    scripts = TaskSettings.get(name="default").scripts or []
    if not scripts:
        logger.warning("No scripts configured")
        return "no_scripts"

    if task.steps_total != len(scripts):
        task.steps_total = len(scripts)
        task.save()

    # если задача уже завершена
    if task.step_index >= task.steps_total:
        logger.info(f"Task {task.id} already finished")
        return "done"

    path = scripts[task.step_index]
    task.step_status = StepStatus.RUNNING
    task.save()
    TaskLogs.create(task_id=task.id, description=f"Start step {task.step_index+1}/{task.steps_total}: {path}")
    logger.info(f"[Task {task.id}] starting {path}")

    code, out, err = run_script(path, task.id)

    if out:
        TaskLogs.create(task_id=task.id, description=out[:2000])
    if code != 0:
        if err:
            TaskLogs.create(task_id=task.id, description=err[:2000])
        task.step_status = StepStatus.ERROR
        task.save()
        logger.error(f"[Task {task.id}] failed {path} exit={code}")
        return f"error:{code}"

    # шаг успешно
    task.step_index += 1
    if task.step_index >= task.steps_total:
        task.step_status = StepStatus.SUCCESS
        TaskLogs.create(task_id=task.id, description="Task finished successfully")
        logger.info(f"[Task {task.id}] finished")
    else:
        task.step_status = StepStatus.WAITING
        TaskLogs.create(task_id=task.id, description=f"Step {path} done, next step pending")
        logger.info(f"[Task {task.id}] step done, waiting next")

    task.save()
    return "ok"
