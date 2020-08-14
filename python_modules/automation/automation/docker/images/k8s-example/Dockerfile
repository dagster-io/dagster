ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

RUN apt-get update -yqq && \
    apt-get install -yqq cron

RUN pip install \
    dagster==${DAGSTER_VERSION} \
    dagster-graphql==${DAGSTER_VERSION} \
    dagster-postgres==${DAGSTER_VERSION} \
    dagster-cron==${DAGSTER_VERSION} \
    dagster-celery[flower,redis,kubernetes]==${DAGSTER_VERSION} \
    dagster-aws==${DAGSTER_VERSION} \
    dagster-k8s==${DAGSTER_VERSION} \
    dagster-celery-k8s==${DAGSTER_VERSION} \
    dagit==${DAGSTER_VERSION}

COPY build_cache/ /
