# Start dashboard
    python run.py

    python run.py --dashboard
    python run.py --celery


# Start celery
    celery -A scheduler.app.celery worker --loglevel=INFO

    celery -A scheduler.app.celery beat --loglevel=INFO --schedule=/tmp/celerybeat-schedule


# Alembic

### Создать новую миграцию
docker compose run --rm migrate alembic revision --autogenerate -m "описание изменений"

### Создать новую миграцию (сравнивает модели и БД):
docker compose run --rm migrate alembic upgrade head

### Откатить до конкретной ревизии
docker compose run --rm migrate alembic downgrade -1

### Откатить до конкретной ревизии
docker compose run --rm migrate alembic downgrade abc123def456

### Применить миграции до конкретной ревизии
docker compose run --rm migrate alembic upgrade abc123def456
