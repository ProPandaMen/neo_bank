from database.base import SessionLocal
from database.models import Task

from database.base import SessionLocal
from database.models import Task


class TaskManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_task(self):
        task = Task()
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_all_tasks(self):
        return self.db.query(Task).order_by(Task.created_at.desc()).all()

    def get_task_by_id(self, task_id):
        return self.db.query(Task).filter(Task.id == task_id).first()

    def close(self):
        self.db.close()
