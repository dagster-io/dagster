FROM python:3.7.5-slim-stretch

ADD build_cache/ /
ADD test_pipelines test_pipelines

ENV GOOGLE_APPLICATION_CREDENTIALS="/gac.json"

RUN pip install --no-deps \
        -e dagster \
        -e dagster-graphql \
        -e dagit \
        -e dagster-aws \
        -e dagster-cron \
        -e dagster-pandas \
        -e dagster-postgres \
        -e dagster-gcp \
        -e dagster-k8s \
        -e dagster-airflow \
        -e test_pipelines \
    && pip install \
        -e dagster \
        -e dagster-graphql \
        -e dagit \
        -e dagster-aws \
        -e dagster-cron \
        -e dagster-pandas \
        -e dagster-postgres \
        -e dagster-gcp \
        -e dagster-k8s \
        -e dagster-airflow \
        -e test_pipelines

WORKDIR /test_pipelines/

EXPOSE 80
