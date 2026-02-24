FROM python:3.12-slim

RUN pip install --no-cache-dir \
    dagster \
    dagster-celery[redis] \
    dagster-postgres \
    dagster-webserver

COPY repo.py /opt/dagster/app/repo.py
# dagster_celery_config.py is auto-imported by dagster_celery to override broker/backend defaults
COPY dagster_celery_config.py /usr/local/lib/python3.12/site-packages/dagster_celery_config.py

WORKDIR /opt/dagster/app

ENV DAGSTER_HOME=/opt/dagster/dagster_home
RUN mkdir -p $DAGSTER_HOME

EXPOSE 4000
