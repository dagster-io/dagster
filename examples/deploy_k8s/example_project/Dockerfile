FROM python:3.7.7

ADD . .

RUN apt-get update -yqq && \
    apt-get install -yqq cron && \
    pip install \
        dagster \
        dagster-graphql \
        dagster-celery[flower,redis,kubernetes] \
        dagster-cron \
        dagit \
        dagster-postgres \
        dagster-aws \
        dagster-k8s
