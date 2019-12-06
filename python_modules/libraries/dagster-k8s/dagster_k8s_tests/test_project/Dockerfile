FROM python:3.7.4-slim-stretch

WORKDIR /opt/dagster

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagit dagit
ADD dagster-postgres dagster-postgres
ADD dagster-aws dagster-aws
ADD dagster-cron dagster-cron
ADD dagster-gcp dagster-gcp
ADD dagster-k8s dagster-k8s
ADD examples examples

RUN pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagit \
    -e dagster-postgres \
    -e dagster-cron \
    -e dagster-aws \
    -e dagster-gcp \
    -e dagster-k8s \
    -e "examples[full]"

EXPOSE 80

WORKDIR /opt/dagster/examples/dagster_examples/toys
