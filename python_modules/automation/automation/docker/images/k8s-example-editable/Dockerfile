ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

RUN apt-get update -yqq && \
    apt-get install -yqq cron

COPY build_cache/ /

RUN pip install \
    -e dagster \
    -e dagster-postgres \
    -e dagster-cron \
    -e dagster-celery[flower,redis,kubernetes] \
    -e dagster-aws \
    -e dagster-k8s \
    -e dagster-celery-k8s
