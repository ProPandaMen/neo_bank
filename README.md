# Start dashboard
    python run.py


# Start celery
    celery -A scheduler.app.celery worker --loglevel=INFO

    celery -A scheduler.app.celery beat --loglevel=INFO --schedule=/tmp/celerybeat-schedule
