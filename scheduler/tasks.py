from sqlalchemy import or_

from scheduler.celery_app import celery_app as celery
from scheduler.scheduling import utcnow, next_fire
from database.base import SessionLocal
from database.models.task import JobSchedule, JobRun, ConflictPolicy, Task, RunState

import subprocess
import datetime
import sys


def run_module(module: str, task_id: int, timeout: int | None = None):
    # Запускаем шаг как модуль: python -m <module> <task_id>
    cmd = [sys.executable, "-m", module, str(task_id)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    return proc.returncode, proc.stdout, proc.stderr


"""
Планировщик
"""
@celery.task(name="scheduler.tick")
def tick():
    # Планировщик: находим «просроченные» расписания и безопасно ставим новые прогоны
    now = utcnow()
    with SessionLocal() as db:
        # Берём максимум 50 подходящих расписаний
        # Важно: for_update + skip_locked -> параллельные тикеры не схватят одни и те же строки
        due = JobSchedule.filter_ex(
            where=[
                JobSchedule.enabled.is_(True),
                JobSchedule.next_run_at.isnot(None),
                JobSchedule.next_run_at <= now,
                or_(JobSchedule.locked_until.is_(None), JobSchedule.locked_until < now),
            ],
            order_by=JobSchedule.next_run_at.asc(),
            limit=50,
            for_update=True,
            skip_locked=True,
            db=db,
        )

        enqueued = 0
        for s in due:
            # Контроль конкуренции: если уже идёт max_instances и политика SKIP — отложим проверку
            active = JobRun.filter_ex(
                where=[JobRun.schedule_id == s.id, JobRun.state == RunState.RUNNING],
                db=db,
            )
            if len(active) >= s.max_instances and s.policy == ConflictPolicy.SKIP:
                s.locked_until = now + datetime.timedelta(seconds=5)
                db.commit()
                continue

            # Снимок пайплайна берём из kwargs.pipeline
            pipeline = (s.kwargs or {}).get("pipeline", [])

            # Создаём прогон и связанный Task
            run = JobRun.create(schedule_id=s.id, state=RunState.QUEUED, attempt=0)
            task = Task.create(
                state=RunState.QUEUED,
                step_index=0,
                steps_total=len(pipeline),
                step_name=None,
                pipeline=pipeline,
            )
            run.task_id = task.id

            # Запланируем следующее время запуска и отправим задачу исполнителю
            s.last_run_at = now
            s.next_run_at = next_fire(s, now)
            s.locked_until = None
            db.commit()

            celery.send_task(
                s.task_name or "scheduler.execute_pipeline",
                args=[run.id],
                queue=s.queue or "executor",
            )
            enqueued += 1

        return enqueued


"""
Исполнитель
"""
@celery.task(bind=True, name="scheduler.execute_pipeline")
def execute_pipeline(self, run_id: int):
    # Исполнитель: последовательно проходит по шагам из Task.pipeline
    hostname = self.request.hostname
    with SessionLocal() as db:
        run = JobRun.get(id=run_id)
        if not run:
            return "missing"

        task = Task.get(id=run.task_id) if run.task_id else None
        if not task:
            # На всякий случай восстановим pipeline из расписания, если task ещё не создан
            sched = JobSchedule.get(id=run.schedule_id)
            pipeline = (sched.kwargs or {}).get("pipeline", []) if sched else []
            task = Task.create(state=RunState.QUEUED, step_index=0, steps_total=len(pipeline), pipeline=pipeline)
            run.task_id = task.id
            run.save()

        pipeline = task.pipeline or []
        total = len(pipeline)

        # Фиксируем старт прогона и захватываем task «на выполнение»
        run.state = RunState.RUNNING
        run.started_at = datetime.datetime.utcnow()
        run.save()

        task.state = RunState.RUNNING
        task.locked_by = hostname
        task.locked_at = datetime.datetime.utcnow()
        task.add_log("pipeline start")

        i = task.step_index or 0  # продолжим с места падения, если было
        try:
            while i < total:
                step = pipeline[i]
                name = step.get("name") or f"step_{i+1}"
                module = step.get("module")

                # Обновим прогресс перед запуском шага
                task.step_index = i
                task.steps_total = total
                task.step_name = name
                task.add_log(f"{name} start")

                # Запустим модуль шага; stdout/stderr сложим в логи
                code, out, err = run_module(module, task.id)
                if out:
                    task.add_log(out[:2000])  # защита от слишком длинных логов
                if code != 0:
                    if err:
                        task.add_log(err[:2000])
                    raise RuntimeError(f"{name} failed with exit {code}")

                task.add_log(f"{name} done")
                task.save()
                i += 1

            # Все шаги прошли — помечаем успех
            task.step_index = total
            task.step_name = "finished"
            task.state = RunState.SUCCESS
            task.locked_by = None
            task.locked_at = None
            task.error = None
            task.add_log("pipeline finished")
            task.save()

            run.state = RunState.SUCCESS
            run.finished_at = datetime.datetime.utcnow()
            run.save()
            return "ok"

        except Exception as e:
            # Ошибка шага — фиксируем падение и отдаём на ретрай `retry_tick`
            task.state = RunState.FAILED
            task.locked_by = None
            task.locked_at = None
            task.error = str(e)
            task.add_log(f"pipeline failed: {e}")
            task.save()

            run.state = RunState.FAILED
            run.error = str(e)
            run.finished_at = datetime.datetime.utcnow()
            run.save()
            raise


"""
Реаниматор
"""
@celery.task(name="scheduler.retry_tick")
def retry_tick():
    # Ретраи: пробегаемся по упавшим прогонaм и ставим повтор на основе настроек расписания
    now = utcnow()
    failed = JobRun.filter(where={"state": RunState.FAILED}, limit=100)
    restarted = 0
    for run in failed:
        sched = JobSchedule.get(id=run.schedule_id)
        if not sched:
            continue

        # Проверяем лимит попыток
        if run.attempt >= sched.retry_limit:
            continue

        # Экспоненциальный бэкофф в пределах backoff_max
        delay = min(sched.backoff_initial * (2 ** max(run.attempt - 1, 0)), sched.backoff_max)

        # Сбрасываем состояние прогона и ставим на повтор
        run.state = RunState.QUEUED
        run.attempt = (run.attempt or 0) + 1
        run.error = None
        run.started_at = None
        run.finished_at = None
        run.save()

        celery.send_task(
            sched.task_name or "scheduler.execute_pipeline",
            args=[run.id],
            queue=sched.queue or "executor",
            countdown=delay,
        )
        restarted += 1

    return restarted
