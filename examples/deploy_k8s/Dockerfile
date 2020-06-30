FROM python:3.7.7

RUN apt-get update -yqq && \
    apt-get install -yqq cron && \
    pip install \
        dagster \
        dagster-graphql \
        dagster-celery[flower,redis,kubernetes] \
        dagster-cron \
        dagster-postgres \
        dagster-aws \
        dagster-k8s