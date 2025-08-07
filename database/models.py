from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import enum
import datetime


Base = declarative_base()


class StepStatus(enum.Enum):
    in_progress = "in_progress"
    success = "success"
    failed = "failed"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    gologin_profile_id = Column(String(128), nullable=True)
    phone_number = Column(String(32), nullable=True)

    steps = relationship("TaskStep", back_populates="task", cascade="all, delete-orphan")


class TaskStep(Base):
    __tablename__ = "task_steps"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(StepStatus), default=StepStatus.in_progress)
    finished_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="steps")
