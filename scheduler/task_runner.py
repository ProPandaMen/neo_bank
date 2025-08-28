from typing import Tuple, Optional
from scheduler.celery_app import celery_app

from celery.utils.log import get_task_logger
from utils.task_logging import log_celery

from database.models.task import Task, TaskLogs, StepStatus, TaskSettings

import subprocess
import datetime
import sys


logger = get_task_logger(__name__)


def get_settings() -> dict:
    ts = TaskSettings.get(name="default") or TaskSettings.create(name="default", scripts=[])

    return {
        "scripts": list(ts.scripts or []),
        "step_timeout": int(ts.step_timeout or 3600),
        "retry_limit": int(ts.retry_limit or 3),
        "backoff_initial": int(ts.backoff_initial or 60),
        "backoff_factor": float(ts.backoff_factor or 2.0),
        "backoff_max": int(ts.backoff_max or 3600),
    }


def run_script(path: str, task_id: int) -> Tuple[int, str, str]:
    cmd = [sys.executable, path, str(task_id)] if path.endswith(".py") else [path, str(task_id)]
    print("RUN:", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)

    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


def fetch_task(task_id: int) -> Optional[Task]:
    return Task.get(id=task_id)


def lock_task(t: Task, hostname: str, timeout_sec: int) -> datetime.datetime:
    now = datetime.datetime.utcnow()
    t.locked_by = hostname
    t.locked_until = now + datetime.timedelta(seconds=timeout_sec)
    t.step_started_at = now
    t.step_status = StepStatus.RUNNING
    t.save()

    return now


def unlock_task(t: Task) -> None:
    t.locked_by = None
    t.locked_until = None
    t.save()


def record_streams(task_id: int, out: str, err: str) -> None:
    if out:
        TaskLogs.create(task_id=task_id, description=out)
        log_celery(task_id, "stdout", out)
    if err:
        TaskLogs.create(task_id=task_id, description=err)
        log_celery(task_id, "stderr", err)


def compute_backoff(cfg: dict, attempts: int) -> int:
    delay = int(cfg["backoff_initial"] * (cfg["backoff_factor"] ** max(attempts - 1, 0)))

    return min(delay, int(cfg["backoff_max"]))


def handle_failure(t: Task, code: int, err: str, cfg: dict, now: datetime.datetime) -> str:
    t.step_status = StepStatus.ERROR
    t.step_attempts = int(t.step_attempts or 0) + 1
    t.last_error = err if err else f"exit {code}"
    delay = compute_backoff(cfg, t.step_attempts)
    t.next_attempt_at = now + datetime.timedelta(seconds=delay)

    unlock_task(t)
    log_celery(t.id, "ошибка", f"Код {code}. Попытка {t.step_attempts}. Повтор через {delay}с")

    logger.info(f"❌ Завершение task_execute с ошибкой (код {code}, попытка {t.step_attempts})")

    return f"error:{code}"


def handle_success(t: Task, path: str) -> None:
    t.step_index += 1
    t.step_attempts = 0
    t.next_attempt_at = None
    t.last_error = None

    if t.step_index >= t.steps_total:
        t.step_status = StepStatus.SUCCESS
        TaskLogs.create(task_id=t.id, description="finished")
        log_celery(t.id, "завершение", "Все шаги выполнены успешно")
    else:
        t.step_status = StepStatus.WAITING
        TaskLogs.create(task_id=t.id, description=f"done: {path}")
        log_celery(t.id, "выполнение", f"Завершён шаг: {path}. Следующий {t.step_index+1}/{t.steps_total}")

    unlock_task(t)


def ensure_steps_total(t: Task, scripts: list) -> None:
    if t.steps_total != len(scripts):
        t.steps_total = len(scripts)
        t.save()
        log_celery(t.id, "инициализация", f"Обновлено число шагов: {t.steps_total}")


def can_skip(t: Task) -> bool:
    return t.step_index >= t.steps_total


def current_script(t: Task, scripts: list) -> str:
    return scripts[t.step_index]


@celery_app.task(name="scheduler.task_execute", bind=True)
def task_execute(self, task_id: int):
    log_celery(task_id, "старт", f"Запуск задачи ID {task_id}")

    cfg = get_settings()
    t = fetch_task(task_id)

    if not t:
        log_celery(task_id, "проверка", "Задача не найдена")
        return "missing"
    
    scripts = cfg["scripts"]

    if not scripts:
        log_celery(task_id, "инициализация", "Скрипты не заданы")
        return "no_scripts"
    
    ensure_steps_total(t, scripts)

    if can_skip(t):
        log_celery(task_id, "завершение", "Все шаги уже выполнены")
        return "done"
    
    hostname = getattr(self.request, "hostname", "executor")
    now = lock_task(t, hostname, cfg["step_timeout"])
    log_celery(task_id, "блокировка", f"Заблокировано воркером {hostname} до {t.locked_until.isoformat()}Z")

    path = current_script(t, scripts)
    log_celery(task_id, "выполнение", f"Старт шага: {t.step_index+1}/{t.steps_total}\n{path}\nID {t.id}")

    code, out, err = run_script(path, t.id)
    record_streams(t.id, out, err)

    if code != 0:
        return handle_failure(t, code, err, cfg, now)
    
    handle_success(t, path)
    
    return "ok"
