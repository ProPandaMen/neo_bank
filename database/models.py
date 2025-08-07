from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import enum
import datetime


Base = declarative_base()


class TaskStatus(enum.Enum):
    CREATED = "created"
    PREPARING = "preparing"
    REGISTERING = "registering"
    GETTING_CARD = "getting_card"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
    gologin_profile_id = Column(String(128), nullable=True)
    phone_number = Column(String(32), nullable=True)

    logs = relationship("TaskLogs", back_populates="task", cascade="all, delete-orphan")


class TaskLogs(Base):
    __tablename__ = "task_logs"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text)

    task = relationship("Task", back_populates="logs")
