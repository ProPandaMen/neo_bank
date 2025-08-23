from dotenv import load_dotenv

import os

load_dotenv(override=True)

"""
# Celery
"""
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL")


"""
# DATABASE
"""
DATABASE_URL = os.getenv("DATABASE_URL")


"""
# Proxy
"""
PROXY_MODE = os.getenv("PROXY_MODE")
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = int(os.getenv("PROXY_PORT"))
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")
PROXY_CHANGE_IP_URL = os.getenv("PROXY_CHANGE_IP_URL")
