FROM python:3.11.5-alpine3.18 AS builder

ENV PYTHONUNBUFFERED 1

RUN apk update && apk add --no-cache build-base curl gcc musl-dev openssl-dev libffi-dev

RUN apk --no-cache add \
  libffi-dev \
  pkgconfig \
  && rm -rf /var/cache/apk/*

ENV PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig

RUN apk add --no-cache git

RUN apk update && \
    apk add --no-cache postgresql-client build-base postgresql-dev linux-headers

COPY ./requirements.txt /requirements.txt

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /requirements.txt --use-pep517

RUN /py/bin/pip install "git+https://github.com/saurav-codes/django-cryptography"

FROM builder AS deploy

COPY ./app /app
COPY ./scripts /scripts
COPY ./compose/celery/start_worker /start-celeryworker
COPY ./compose/celery/start_beat /start-celerybeat

WORKDIR /app

RUN adduser --disabled-password --gecos '' djuser && \
    chown -R djuser:djuser /app && \
    mkdir -p /app/vol && \
    mkdir -p /app/vol /app/logs/info /app/logs/warning /app/logs/error /app/logs/critical && \
    chmod -R 755 /app && \
    chmod -R a+rw /app/logs/info /app/logs/warning /app/logs/error /app/logs/critical && \
    chmod -R +x /scripts && \
    chown -R djuser:djuser /start-celeryworker && \
    sed -i 's/\r$//g' /start-celeryworker && \
    chmod +x /start-celeryworker && \
    chown -R djuser:djuser /start-celerybeat && \
    sed -i 's/\r$//g' /start-celerybeat && \
    chmod +x /start-celerybeat 

ENV PATH="/scripts:/py/bin:$PATH"

CMD ["run.sh"]
