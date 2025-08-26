# Start dashboard
    python run.py

    python run.py --dashboard
    python run.py --celery


# Start celery
    celery -A scheduler.app.celery worker --loglevel=INFO

    celery -A scheduler.app.celery beat --loglevel=INFO --schedule=/tmp/celerybeat-schedule


# Alembic

### Создать новую миграцию
docker exec -it neo_bank-dashboard-1 alembic revision --autogenerate -m "описание изменений"

### Создать новую миграцию (сравнивает модели и БД):
docker exec -it neo_bank-dashboard-1 alembic upgrade head

### Откатить до конкретной ревизии
docker exec -it neo_bank-dashboard-1 alembic downgrade -1

### Откатить до конкретной ревизии
docker exec -it neo_bank-dashboard-1 alembic downgrade abc123def456

### Применить миграции до конкретной ревизии
docker exec -it neo_bank-dashboard-1 alembic upgrade abc123def456
