from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship

from database.base import Base
from database.models.base import BaseModel

import enum
import datetime


class TaskStatus(enum.Enum):
    CREATED = "created"
    PREPARING = "preparing"
    REGISTERING = "registering"
    GETTING_CARD = "getting_card"


class Task(BaseModel, Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    gologin_profile_id = Column(String(128), nullable=True)
    phone_number = Column(String(32), nullable=True)
    logs = relationship("TaskLogs", back_populates="task", cascade="all, delete-orphan")

    def add_log(self, description):
        TaskLogs.create(task_id=self.id, description=description)


class TaskLogs(BaseModel, Base):
    __tablename__ = "task_logs"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)
    task = relationship("Task", back_populates="logs")
