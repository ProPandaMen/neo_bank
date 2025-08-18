from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from database.base import Base
from database.models.base import BaseModel

import enum
import datetime


class RunState(enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"


class Task(BaseModel, Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)

    # Время создания
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    # Текущий статус
    state = Column(Enum(RunState), default=RunState.QUEUED, nullable=False)

    # Номер текущего шага (0-based)
    step_index = Column(Integer, default=0, nullable=False)
    # Общее кол-во шагов в пайплайне на момент старта
    steps_total = Column(Integer, default=0, nullable=False)
    # Человекочитаемое имя текущего шага
    step_name = Column(String(128), nullable=True)

    # Снимок последовательности шагов: [{name, module}, ...]
    pipeline = Column(JSON, nullable=True)

    # Данные карты
    card_number = Column(String(30), nullable=True)
    card_date = Column(String(10), nullable=True)
    card_cvv = Column(String(10), nullable=True)

    # Какой воркер/хост сейчас исполняет
    locked_by = Column(String(64), nullable=True)
    # Момент захвата задачи воркером
    locked_at = Column(DateTime, nullable=True)
    # Текст последней ошибки, если упала
    error = Column(Text, nullable=True)

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


class ScheduleType(enum.Enum):
    CRON = "cron"
    INTERVAL = "interval"
    ONEOFF = "oneoff"


class ConflictPolicy(enum.Enum):
    ENQUEUE = "enqueue"
    SKIP = "skip"


class JobSchedule(BaseModel, Base):
    __tablename__ = "job_schedules"
    id = Column(Integer, primary_key=True)

    # Уникальное имя расписания (для дашборда/поиска)
    name = Column(String(128), unique=True, nullable=False)

    # Celery-задача-исполнитель (обычно scheduler.execute_pipeline)
    task_name = Column(String(256), nullable=False)
    # Очередь Celery для запусков
    queue = Column(String(64), nullable=True)

    # Позиционные аргументы для Celery-задачи
    args = Column(JSON, default=list, nullable=False)
    # Именованные аргументы (сюда кладём pipeline)
    kwargs = Column(JSON, default=dict, nullable=False)

    # Тип расписания: CRON/INTERVAL/ONEOFF
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    # CRON-выражение (если CRON)
    cron_expr = Column(String(128), nullable=True)
    # Интервал в секундах (если INTERVAL)
    interval_seconds = Column(Integer, nullable=True)
    # Таймзона для CRON
    timezone = Column(String(64), default="UTC", nullable=False)

    # Включено/выключено
    enabled = Column(Boolean, default=True, nullable=False)
    # Одновременных прогонов по этому расписанию
    max_instances = Column(Integer, default=1, nullable=False)
    # Поведение при занятости: SKIP/ENQUEUE
    policy = Column(Enum(ConflictPolicy), default=ConflictPolicy.SKIP, nullable=False)
    # Случайный сдвиг запуска, сглаживание пиков
    jitter_seconds = Column(Integer, default=0, nullable=False)

    # Макс. число ретраев для каждого прогона
    retry_limit = Column(Integer, default=3, nullable=False)
    # Стартовая задержка ретрая (сек)
    backoff_initial = Column(Integer, default=30, nullable=False)
    # Верхняя граница бэкоффа (сек)
    backoff_max = Column(Integer, default=3600, nullable=False)

    # Время последнего запуска
    last_run_at = Column(DateTime, nullable=True)
    # Следующее запланированное время
    next_run_at = Column(DateTime, nullable=True)
    
    # Внутренний «замок» тика, чтобы не дергать одно и то же
    locked_until = Column(DateTime, nullable=True)

    runs = relationship("JobRun", back_populates="schedule", cascade="all, delete-orphan")


class JobRun(BaseModel, Base):
    __tablename__ = "job_runs"
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("job_schedules.id"), index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), index=True, nullable=True)

    # Время создания прогона
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    # Время фактического старта
    started_at = Column(DateTime, nullable=True)
    # Время завершения
    finished_at = Column(DateTime, nullable=True)

    # Состояние прогона: QUEUED/RUNNING/FAILED/SUCCESS
    state = Column(Enum(RunState), default=RunState.QUEUED, nullable=False)
    # Номер попытки (для ретраев)
    attempt = Column(Integer, default=0, nullable=False)
    # Когда можно повторить (если используется отложенный ретрай)
    next_retry_at = Column(DateTime, nullable=True)
    # Короткое описание ошибки последней попытки
    error = Column(String(2000), nullable=True)

    schedule = relationship("JobSchedule", back_populates="runs")
