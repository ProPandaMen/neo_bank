import subprocess
import datetime
import sys
import logging
from sqlalchemy import or_

from scheduler.celery_app import celery_app as celery
from scheduler.scheduling import utcnow, next_fire
from database.base import SessionLocal
from database.models.task import JobSchedule, JobRun, ConflictPolicy, Task, RunState


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_module(module: str, task_id: int, timeout: int | None = None):
    cmd = [sys.executable, "-m", module, str(task_id)]
    logger.info(f"Запуск модуля {module} для task_id={task_id}")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


@celery.task(name="scheduler.scheduler_tick")
def scheduler_tick():
    logger.info("▶️ scheduler_tick запущен")
    now = utcnow()
    with SessionLocal() as db:
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
            active = JobRun.filter_ex(
                where=[JobRun.schedule_id == s.id, JobRun.state == RunState.RUNNING],
                db=db,
            )
            if len(active) >= s.max_instances and s.policy == ConflictPolicy.SKIP:
                logger.info(f"⏸ Пропускаем {s.name}, занято {len(active)} инстансов")
                s.locked_until = now + datetime.timedelta(seconds=5)
                db.commit()
                continue

            pipeline = (s.kwargs or {}).get("pipeline", [])
            run = JobRun.create(schedule_id=s.id, state=RunState.QUEUED, attempt=0)
            task = Task.create(
                state=RunState.QUEUED,
                step_index=0,
                steps_total=len(pipeline),
                step_name=None,
                pipeline=pipeline,
            )
            run.task_id = task.id

            s.last_run_at = now
            s.next_run_at = next_fire(s, now)
            s.locked_until = None
            db.commit()

            celery.send_task(
                s.task_name or "scheduler.pipeline_execute",
                args=[run.id],
                queue=s.queue or "executor",
            )
            logger.info(f"🚀 Отправлен pipeline {s.name} (run_id={run.id})")
            enqueued += 1

        logger.info(f"✅ scheduler_tick завершён, поставлено {enqueued} задач")
        return enqueued


@celery.task(bind=True, name="scheduler.pipeline_execute")
def pipeline_execute(self, run_id: int):
    logger.info(f"▶️ pipeline_execute запущен (run_id={run_id}) на {self.request.hostname}")
    hostname = self.request.hostname
    with SessionLocal() as db:
        run = JobRun.get(id=run_id)
        if not run:
            logger.warning(f"❌ Run {run_id} не найден")
            return "missing"

        task = Task.get(id=run.task_id) if run.task_id else None
        if not task:
            sched = JobSchedule.get(id=run.schedule_id)
            pipeline = (sched.kwargs or {}).get("pipeline", []) if sched else []
            task = Task.create(state=RunState.QUEUED, step_index=0, steps_total=len(pipeline), pipeline=pipeline)
            run.task_id = task.id
            run.save()

        pipeline = task.pipeline or []
        total = len(pipeline)

        run.state = RunState.RUNNING
        run.started_at = datetime.datetime.utcnow()
        run.save()

        task.state = RunState.RUNNING
        task.locked_by = hostname
        task.locked_at = datetime.datetime.utcnow()
        task.add_log("pipeline start")

        i = task.step_index or 0
        try:
            while i < total:
                step = pipeline[i]
                name = step.get("name") or f"step_{i+1}"
                module = step.get("module")

                task.step_index = i
                task.steps_total = total
                task.step_name = name
                task.add_log(f"{name} start")
                logger.info(f"▶️ Шаг {i+1}/{total}: {name} (модуль={module})")

                code, out, err = run_module(module, task.id)
                if out:
                    task.add_log(out[:2000])
                    logger.info(f"ℹ️ stdout: {out[:200].strip()}...")
                if code != 0:
                    if err:
                        task.add_log(err[:2000])
                        logger.error(f"❌ stderr: {err[:200].strip()}...")
                    raise RuntimeError(f"{name} failed with exit {code}")

                task.add_log(f"{name} done")
                task.save()
                logger.info(f"✅ Шаг {name} завершён")
                i += 1

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
            logger.info(f"🎉 pipeline_execute run_id={run_id} завершён успешно")
            return "ok"

        except Exception as e:
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
            logger.error(f"🔥 pipeline_execute run_id={run_id} упал: {e}")
            raise


@celery.task(name="scheduler.scheduler_retry")
def scheduler_retry():
    logger.info("▶️ scheduler_retry запущен")
    failed = JobRun.filter(state=RunState.FAILED, limit=100)
    restarted = 0
    for run in failed:
        sched = JobSchedule.get(id=run.schedule_id)
        if not sched:
            continue

        if run.attempt >= sched.retry_limit:
            logger.info(f"⏭ Пропускаем run_id={run.id}, достигнут лимит ретраев")
            continue

        delay = min(sched.backoff_initial * (2 ** max(run.attempt - 1, 0)), sched.backoff_max)

        run.state = RunState.QUEUED
        run.attempt = (run.attempt or 0) + 1
        run.error = None
        run.started_at = None
        run.finished_at = None
        run.save()

        celery.send_task(
            sched.task_name or "scheduler.pipeline_execute",
            args=[run.id],
            queue=sched.queue or "executor",
            countdown=delay,
        )
        restarted += 1
        logger.info(f"🔄 run_id={run.id} отправлен на повтор через {delay}с")

    logger.info(f"✅ scheduler_retry завершён, перезапущено {restarted} задач")
    return restarted
