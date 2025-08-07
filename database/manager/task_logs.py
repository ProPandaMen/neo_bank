from database.base import SessionLocal
from database.models import TaskLogs


class TaskLogsManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_log(self, task_id, description):
        log = TaskLogs(
            task_id=task_id,
            description=description
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_logs_by_task(self, task_id):
        return self.db.query(TaskLogs).filter(TaskLogs.task_id == task_id).order_by(TaskLogs.created_at).all()

    def close(self):
        self.db.close()
