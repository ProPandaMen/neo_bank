# Start dashboard
    python run.py

    python run.py --dashboard
    python run.py --celery


# Start celery
    celery -A scheduler.app.celery worker --loglevel=INFO

    celery -A scheduler.app.celery beat --loglevel=INFO --schedule=/tmp/celerybeat-schedule
