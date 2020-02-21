ARG PYTHON_VERSION

FROM python:"${PYTHON_VERSION}"

ADD build_cache/ /
ADD test_pipelines test_pipelines

ENV GOOGLE_APPLICATION_CREDENTIALS="/gac.json"

RUN apt-get update -yqq && \
    apt-get install -yqq cron && \
    pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagster-celery[flower] \
    -e dagster-cron \
    -e dagit \
    -e dagster-postgres \
    -e dagster-pandas \
    -e dagster-aws \
    -e dagster-gcp \
    -e dagster-k8s \
    -e dagster-airflow \
    -e test_pipelines

WORKDIR /test_pipelines/

EXPOSE 80
