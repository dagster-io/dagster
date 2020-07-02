ARG PYTHON_VERSION

FROM python:"${PYTHON_VERSION}"

ADD build_cache/ /
ADD . .

ENV GOOGLE_APPLICATION_CREDENTIALS="/gac.json"

RUN apt-get update -yqq && \
    apt-get install -yqq cron && \
    pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagster-celery[flower,redis,kubernetes] \
    -e dagster-cron \
    -e dagit \
    -e dagster-postgres \
    -e dagster-pandas \
    -e dagster-aws \
    -e dagster-gcp \
    -e dagster-k8s \
    -e dagster-celery-k8s \
    -e dagster-airflow \
    -e .

WORKDIR /dagster_test/test_project/

EXPOSE 80
