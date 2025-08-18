from database.base import SessionLocal
from scheduler.tasks import tick, execute_pipeline, retry_tick
from database.models.task import JobSchedule, JobRun, Task, RunState, ConflictPolicy

import datetime


def smoke_planner():
    r = tick.apply().get()
    print("planner:", r)


def smoke_executor_success():
    with SessionLocal() as db:
        sched = JobSchedule.create(
            enabled=True,
            next_run_at=datetime.datetime.utcnow(),
            locked_until=None,
            max_instances=1,
            policy=ConflictPolicy.SKIP,
            kwargs={"pipeline": [{"name": "ok", "module": "tests.dummy_ok"}]}
        )
        run = JobRun.create(schedule_id=sched.id, state=RunState.QUEUED, attempt=0)
        task = Task.create(state=RunState.QUEUED, step_index=0, steps_total=1, pipeline=[{"name":"ok","module":"tests.dummy_ok"}])
        run.task_id = task.id
        run.save()
    r = execute_pipeline.apply(args=[run.id]).get()
    print("executor_success:", r)


def smoke_executor_fail():
    with SessionLocal() as db:
        sched = JobSchedule.create(
            enabled=True,
            next_run_at=datetime.datetime.utcnow(),
            locked_until=None,
            max_instances=1,
            policy=ConflictPolicy.SKIP,
            kwargs={"pipeline": [{"name": "fail", "module": "tests.dummy_fail"}]}
        )
        run = JobRun.create(schedule_id=sched.id, state=RunState.QUEUED, attempt=0)
        task = Task.create(state=RunState.QUEUED, step_index=0, steps_total=1, pipeline=[{"name":"fail","module":"tests.dummy_fail"}])
        run.task_id = task.id
        run.save()
    try:
        execute_pipeline.apply(args=[run.id]).get()
    except Exception as e:
        print("executor_fail:", str(e))


def smoke_resuscitator():
    with SessionLocal() as db:
        sched = JobSchedule.create(
            enabled=True,
            next_run_at=None,
            locked_until=None,
            max_instances=1,
            policy=ConflictPolicy.SKIP,
            retry_limit=3,
            backoff_initial=5,
            backoff_max=60,
            kwargs={"pipeline": [{"name": "ok", "module": "tests.dummy_ok"}]}
        )
        run = JobRun.create(schedule_id=sched.id, state=RunState.FAILED, attempt=0)
    r = retry_tick.apply().get()
    print("resuscitator:", r)


if __name__ == "__main__":
    smoke_planner()
    smoke_executor_success()
    smoke_executor_fail()
    smoke_resuscitator()
