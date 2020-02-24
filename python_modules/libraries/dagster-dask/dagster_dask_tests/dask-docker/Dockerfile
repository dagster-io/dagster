ARG PYTHON_VERSION

FROM python:$PYTHON_VERSION-slim-stretch

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagster-dask dagster-dask
ADD dagster-aws dagster-aws
ADD dagster-cron dagster-cron
ADD examples examples

# Annoyingly, we have to build psutil (no wheels) on slim-stretch
RUN apt-get update \
    && apt-get install -yqq gcc \
    && pip install psutil \
    && apt-get remove -yqq gcc

RUN pip install -e dagster/
RUN pip install -e dagster-graphql/
RUN pip install -e dagster-dask/
RUN pip install -e dagster-aws/
RUN pip install -e dagster-cron/
RUN pip install -e examples/
