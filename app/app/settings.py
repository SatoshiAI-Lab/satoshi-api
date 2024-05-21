"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 5.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import datetime
import os
from pathlib import Path
from typing import Any, Never

from celery import Celery

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR: Path = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY: str | None = os.getenv(key="SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = o=os.getenv(key="DEBUG", default=False)

ALLOWED_HOSTS: list[str] = ["*"]


# Application definition

INSTALLED_APPS: list[str] = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_prometheus",
    "users",
    "subscribe",
    "chat",
    "coin",
    "drf_yasg",
    "cryptography",
    "corsheaders",
    "rest_framework_simplejwt",
]

MIDDLEWARE: list[str] = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

CORS_ORIGIN_ALLOW_ALL: bool = True
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ORIGIN_WHITELIST: tuple[()] = ()
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'VIEW',
)
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'XMLHttpRequest',
    'X_FILENAME',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',
    'sentry-trace',
    'baggage',
    'taloveToken',
)

ROOT_URLCONF: str = "app.urls"

TEMPLATES: list[dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "app.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES: dict[str, dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "HOST": os.getenv(key="POSTGRES_HOST"),
        "PORT": os.getenv(key="POSTGRES_PORT"),
        "NAME": os.getenv(key="POSTGRES_DB"),
        "USER": os.getenv(key="POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "CONN_MAX_AGE": 300,
    },
    "resource": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "HOST": os.getenv(key="RESOURCE_HOST"),
        "PORT": os.getenv(key="RESOURCE_PORT"),
        "NAME": os.getenv(key="RESOURCE_DB"),
        "USER": os.getenv(key="RESOURCE_USER"),
        "PASSWORD": os.getenv(key="RESOURCE_PASSWORD"),
        "CONN_MAX_AGE": 300,
    },
    'coin_source': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        "HOST": os.getenv(key="SOURCE_HOST"),
        "PORT": os.getenv(key="SOURCE_PORT"),
        "NAME": os.getenv(key="SOURCE_DB"),
        "USER": os.getenv(key="SOURCE_USER"),
        "PASSWORD": os.getenv(key="SOURCE_PASSWORD"),
        "CONN_MAX_AGE": 300,
    },
}

DATABASE_ROUTERS: list[str] = ['app.database_router.DatabaseAppsRouter']

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE: str = "en-us"

TIME_ZONE: str = "UTC"

USE_I18N: bool = True

USE_TZ: bool = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL: str = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"


app: Celery = Celery(main="app")
app.config_from_object(obj="django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

CACHES: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv(key="REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 100
            },
            # "PASSWORD": os.getenv("REDIS_PASSWORD"),
        },
    },
}

MEDIA_ROOT: str = os.path.join(BASE_DIR, "vol/")
MEDIA_URL: str = "/media/"

BROKER_URL: str | None = os.getenv(key="REDIS_URL")
CELERY_RESULT_BACKEND: str | None = os.getenv(key="REDIS_URL")
CELERY_ACCEPT_CONTENT: list[str] = ["application/json"]
CELERY_TASK_SERIALIZER: str = "json"
CELERY_RESULT_SERIALIZER: str = "json"
CELERY_TIMEZONE: str | None = os.getenv(key="CELERY_TIMEZONE")

REST_FRAMEWORK: dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    'EXCEPTION_HANDLER': 'utils.response_util.custom_exception_handler',
}

SIMPLE_JWT: dict[str, datetime.timedelta] = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=90),
}

AUTH_USER_MODEL: str = "users.User"

ACCOUNT_AUTHENTICATION_METHOD: str = "email"
ACCOUNT_EMAIL_REQUIRED: bool = True
ACCOUNT_UNIQUE_EMAIL: bool = True
ACCOUNT_USERNAME_REQUIRED: bool = False
APPEND_SLASH: bool = False

ASGI_APPLICATION: str = "app.asgi.application"

CHANNEL_LAYERS: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.environ.get("REDIS_HOST"), os.environ.get("REDIS_PORT"))],
        },
    },
}

LOG_DIR: str = os.path.join(BASE_DIR, "logs")  # Set your log directory as needed

# Ensure the log directory exists
if not os.path.exists(path=LOG_DIR):
    os.makedirs(name=LOG_DIR)

INFO_LOG_DIR: str = os.path.join(LOG_DIR, "info")
WARNING_LOG_DIR: str = os.path.join(LOG_DIR, "warning")
ERROR_LOG_DIR: str = os.path.join(LOG_DIR, "error")
CRITICAL_LOG_DIR: str = os.path.join(LOG_DIR, "critical")

if not os.path.exists(path=INFO_LOG_DIR):
    os.makedirs(name=INFO_LOG_DIR)
if not os.path.exists(path=WARNING_LOG_DIR):
    os.makedirs(name=WARNING_LOG_DIR)
if not os.path.exists(path=ERROR_LOG_DIR):
    os.makedirs(name=ERROR_LOG_DIR)
if not os.path.exists(path=CRITICAL_LOG_DIR):
    os.makedirs(name=CRITICAL_LOG_DIR)

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s|%(asctime)s|%(module)s|%(process)d|%(thread)d|%(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "info_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/info/info_{datetime.datetime.now().strftime('%Y-%m-%d')}.log",
            "when": "midnight",
            "backupCount": 100,
            "formatter": "verbose",
            "interval": 1,
            "delay": True,
        },
        "warning_file": {
            "level": "WARNING",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/warning/warning_{datetime.datetime.now().strftime('%Y-%m-%d')}.log",
            "when": "midnight",
            "backupCount": 100,
            "formatter": "verbose",
            "interval": 1,
            "delay": True,
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/error/error_{datetime.datetime.now().strftime('%Y-%m-%d')}.log",
            "when": "midnight",
            "backupCount": 100,
            "formatter": "verbose",
            "interval": 1,
            "delay": True,
        },
        "critical_file": {
            "level": "CRITICAL",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/critical/critical_{datetime.datetime.now().strftime('%Y-%m-%d')}.log",
            "when": "midnight",
            "backupCount": 100,
            "formatter": "verbose",
            "interval": 1,
            "delay": True,
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "console",
                "info_file",
                "warning_file",
                "error_file",
                "critical_file",
            ],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "console",
                "info_file",
                "warning_file",
                "error_file",
                "critical_file",
                "mail_admins",
            ],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security": {
            "handlers": [
                "console",
                "info_file",
                "warning_file",
                "error_file",
                "critical_file",
                "mail_admins",
            ],
            "level": "ERROR",
            "propagate": True,
        },
        "py.warnings": {
            "handlers": ["console"],
        },
        "django.server": {
            "handlers": [
                "console",
                "info_file",
                "warning_file",
                "error_file",
                "critical_file",
            ],
            "level": "INFO",
            "propagate": True,
        },
    },
}
