FROM python:3.12-slim

RUN pip install --no-cache-dir \
    dagster~=1.12.0 \
    dagster-celery[redis]~=0.28.0 \
    dagster-postgres~=0.28.0 \
    dagster-webserver~=1.12.0

COPY repo.py /opt/dagster/app/repo.py
# dagster_celery_config.py is auto-imported by dagster_celery to override broker/backend defaults
COPY dagster_celery_config.py /usr/local/lib/python3.12/site-packages/dagster_celery_config.py

WORKDIR /opt/dagster/app

ENV DAGSTER_HOME=/opt/dagster/dagster_home
RUN mkdir -p $DAGSTER_HOME

EXPOSE 4000
