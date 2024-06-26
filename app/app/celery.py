import os
from celery import Celery
from celery.schedules import crontab
import datetime


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault(key="DJANGO_SETTINGS_MODULE", value="app.settings")

# Create a Celery application instance
app = Celery(main="app")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(obj="django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Reading environment variables for Celery configuration
BROKER_URL: str | None = os.getenv(key="REDIS_URL")
CELERY_RESULT_BACKEND: str | None = os.getenv(key="REDIS_URL")
CELERY_TIMEZONE: str | None = os.getenv(key="CELERY_TIMEZONE")

# Update Celery configuration with environment variables
app.conf.update(
    BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
    CELERY_TIMEZONE=CELERY_TIMEZONE,
    CELERY_ACCEPT_CONTENT=["application/json"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
    CELERYBEAT_SCHEDULE={
        # 'withdraw-check-task': {
        #     'task': 'users.tasks.check_hash',
        #     'schedule':  datetime.timedelta(seconds=60),
        #     'args': ()
        # },
    }
)