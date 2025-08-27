from celery.utils.log import get_task_logger
from scheduler.celery_app import celery_app

from database.models.task import Task, TaskLogs, StepStatus, TaskSettings

import subprocess
import datetime
import sys


logger = get_task_logger(__name__)


def _settings():
    ts = TaskSettings.get(name="default") or TaskSettings.create(name="default", scripts=[])
    return {
        "scripts": list(ts.scripts or []),
        "step_timeout": int(ts.step_timeout or 3600),
        "retry_limit": int(ts.retry_limit or 3),
        "backoff_initial": int(ts.backoff_initial or 60),
        "backoff_factor": float(ts.backoff_factor or 2.0),
        "backoff_max": int(ts.backoff_max or 3600),
    }


def run_script(path: str, task_id: int):    
    TaskLogs.create(
        task_id=task_id, 
        description=f"Task script start:{path}"
    )

    cmd = [sys.executable, path, str(task_id)] if path.endswith(".py") else [path, str(task_id)]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    TaskLogs.create(
        task_id=task_id, 
        description=f"Task script finish:{path}"
    )
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


@celery_app.task(name="scheduler.task_execute", bind=True)
def task_execute(self, task_id: int):
    logger.info("Start task_execute")

    cfg = _settings()
    t = Task.get(id=task_id)
    if not t:
        logger.error(f"Task {task_id} not found")
        return "missing"
    
    scripts = cfg["scripts"]
    if not scripts:
        TaskLogs.create(task_id=t.id, description="нет скриптов")
        return "no_scripts"
    if t.steps_total != len(scripts):
        t.steps_total = len(scripts)
        t.save()
    if t.step_index >= t.steps_total:
        return "done"

    now = datetime.datetime.utcnow()
    hostname = getattr(self.request, "hostname", "executor")
    t.locked_by = hostname
    t.locked_until = now + datetime.timedelta(seconds=cfg["step_timeout"])
    t.step_started_at = now
    t.step_status = StepStatus.RUNNING
    t.save()

    path = scripts[t.step_index]    
    code, out, err = run_script(path, t.id)

    if out:
        TaskLogs.create(task_id=t.id, description=out[:2000])
    if code != 0:
        if err:
            TaskLogs.create(task_id=t.id, description=err[:2000])
        t.step_status = StepStatus.ERROR
        t.step_attempts = int(t.step_attempts or 0) + 1
        t.last_error = err[:2000] if err else f"exit {code}"
        delay = min(int(cfg["backoff_initial"] * (cfg["backoff_factor"] ** max(t.step_attempts - 1, 0))), int(cfg["backoff_max"]))
        t.next_attempt_at = now + datetime.timedelta(seconds=delay)
        t.locked_by = None
        t.locked_until = None
        t.save()
        return f"error:{code}"

    t.step_index += 1
    t.step_attempts = 0
    t.next_attempt_at = None
    t.last_error = None
    if t.step_index >= t.steps_total:
        t.step_status = StepStatus.SUCCESS
        TaskLogs.create(task_id=t.id, description="finished")
    else:
        t.step_status = StepStatus.WAITING
        TaskLogs.create(task_id=t.id, description=f"done: {path}")
    t.locked_by = None
    t.locked_until = None
    t.save()

    logger.info("Done task_execute")
    return "ok"
