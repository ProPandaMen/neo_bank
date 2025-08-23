from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum as EnumType
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList
from enum import Enum

from database.base import Base
from database.models.base import BaseModel

import datetime


class StepStatus(Enum):
    WAITING = "Ожидание"
    RUNNING = "В работе"
    ERROR = "Ошибка"
    SUCCESS = "Успешно"


class Task(BaseModel, Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)

    # Время создания
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Номер текущего шага (0-based)
    step_index = Column(Integer, default=0, nullable=False)
    # Общее кол-во шагов в пайплайне на момент старта
    steps_total = Column(Integer, default=0, nullable=False)
    # Статус текущего шага
    step_status = Column(
        EnumType(
            StepStatus,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x],
            name="step_status"
        ),
        nullable=False,
        default=StepStatus.WAITING,
        server_default=StepStatus.WAITING.value,
        index=True,
    )

    # Данные карты
    card_number = Column(String(30), nullable=True)
    card_date = Column(String(10), nullable=True)
    card_cvv = Column(String(10), nullable=True)

    logs = relationship("TaskLogs", back_populates="task", cascade="all, delete-orphan")

    def add_log(self, description):
        TaskLogs.create(task_id=self.id, description=description)


class TaskLogs(BaseModel, Base):
    __tablename__ = "task_logs"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))

    # Время записи
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    # Сообщение лога
    description = Column(Text, nullable=False)

    task = relationship("Task", back_populates="logs")


class TaskSettings(Base, BaseModel):
    __tablename__ = "task_settings"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    scripts = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
