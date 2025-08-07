from .base import SessionLocal
from .models import Task, TaskStep, PhoneProfile, TaskStatus

import datetime


class TaskManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_task(self):
        task = Task(status=TaskStatus.new)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def add_step(self, task_id, step_number, status="new", data=None):
        step = TaskStep(
            task_id=task_id,
            step_number=step_number,
            status=status,
            data=data or {},
            started_at=datetime.datetime.utcnow()
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def update_step(self, step_id, status=None, error_message=None, data=None, finished=False):
        step = self.db.query(TaskStep).filter_by(id=step_id).first()
        if status:
            step.status = status
        if error_message:
            step.error_message = error_message
        if data is not None:
            step.data = data
        if finished:
            step.finished_at = datetime.datetime.utcnow()
        self.db.commit()
        return step

    def set_phone_profile(self, task_id, phone_number, proxy, gologin_profile_id):
        profile = PhoneProfile(
            task_id=task_id,
            phone_number=phone_number,
            proxy=proxy,
            gologin_profile_id=gologin_profile_id
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_task(self, task_id):
        return self.db.query(Task).filter_by(id=task_id).first()

    def get_all_tasks(self):
        return self.db.query(Task).order_by(Task.created_at.desc()).all()
