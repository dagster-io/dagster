ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

# remove once daemon scheduler is default
RUN apt-get update -yqq && \
    apt-get install -yqq --no-install-recommends cron

COPY build_cache/ /

RUN pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagster-postgres \
    -e dagster-cron \
    -e dagster-k8s \
    -e dagster-aws \
    -e dagit