import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

# Create a Celery application instance
app = Celery("app")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Reading environment variables for Celery configuration
BROKER_URL = os.getenv("REDIS_URL")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE")

# Update Celery configuration with environment variables
app.conf.update(
    BROKER_URL=BROKER_URL,
    CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
    CELERY_TIMEZONE=CELERY_TIMEZONE,
    CELERY_ACCEPT_CONTENT=["application/json"],
    CELERY_TASK_SERIALIZER="json",
    CELERY_RESULT_SERIALIZER="json",
)
