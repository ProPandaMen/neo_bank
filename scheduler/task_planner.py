from celery.utils.log import get_task_logger
from sqlalchemy import and_

from utils.task_logging import log_celery
from scheduler.celery_app import celery_app
from database.models.task import Task, StepStatus, TaskSettings

from datetime import datetime, timedelta


logger = get_task_logger(__name__)


@celery_app.task(name="scheduler.task_planner")
def task_planner():
    logger.info("Start planner")

    task_setting = TaskSettings.get(name="default")

    # Скрипты для выполнения
    scripts = task_setting.scripts
    # Максимальное кол-во одновременных задач
    parallel_limit = task_setting.parallel_limit
    # Кол-во задач создаваемых за один раз 
    create_batch = task_setting.create_batch
    # Время жизни задачи
    step_timeout = task_setting.step_timeout
    # Максимальное кол-во попыток запуска
    retry_limit = task_setting.retry_limit

    # Включение/выключение планировщика
    planer_enabled = task_setting.planer_enabled
    
    # Запущенные задачи
    running = Task.filter(step_status=StepStatus.RUNNING)
    # Доступная ёмкость для новых задач
    capacity = max(0, parallel_limit - len(running))

    # Начальная задержка (сек)
    backoff_initial = task_setting.backoff_initial
    # Коэффициент роста задержки
    backoff_factor = task_setting.backoff_factor
    # Макс. задержка (сек)
    backoff_max = task_setting.backoff_max

    # Результаты планировщика
    # Запущенные задачи
    started = 0
    # Повторные попытки
    retried = 0
    # Новые задачи
    created = 0

    # Планировщик выключен — вернуть статистику
    if not planer_enabled:
        return {
            "started": started,
            "retried": retried,
            "created": created
        }

    # Просроченные задачи (RUNNING, но вышел таймаут)
    expired = Task.filter_ex(
        where=[and_(
            Task.step_status == StepStatus.RUNNING,
            Task.next_attempt_at < datetime.utcnow() - timedelta(seconds=step_timeout)
        )]
    )

    for task in expired:
        task.step_status = StepStatus.ERROR
        log_celery(task.id, "Ошибка", "Задача просрочена планировщиком")


    # Запуск ожидающих задач
    if capacity > 0:        
        ready = Task.filter_ex(
            where=[and_(
                Task.step_index < Task.steps_total, 
                Task.step_status == StepStatus.WAITING)
            ], 
            order_by=Task.created_at.asc(), limit=capacity
        )

        for task in ready:
            celery_app.send_task("scheduler.task_execute", args=[task.id], queue="executor")
            started += 1

        capacity -= started


     # Повторный запуск упавших задач
    if capacity > 0:
        failed = Task.filter(
            step_status=StepStatus.ERROR,
            order_by=Task.created_at.asc(),
            limit=capacity
        )

        launched = 0
        for task in failed:
            if task.step_attempts >= retry_limit:
                continue

            delay = min(backoff_max, int(backoff_initial * (backoff_factor ** task.step_attempts)))            
            celery_app.send_task(
                "scheduler.task_execute",
                args=[task.id],
                queue="executor",
                countdown=delay
            )
            
            task.step_attempts += 1
            task.save()

            log_celery(task.id, "Повторный запуск", f"попытка {task.step_attempts}, задержка {delay}с")
            retried += 1
            launched += 1

        capacity -= launched


    # Создание новых задач
    if capacity > 0 and scripts:
        n = min(create_batch, capacity)
        for _ in range(n):
            task = Task.create(
                step_index=0, 
                steps_total=len(scripts), 
                step_status=StepStatus.WAITING
            )
            log_celery(task.id, "Создание", "Автоматически создаем новую задачу")
            created += 1
    

    return {
        "started": started,
        "retried": retried,
        "created": created
    }
