ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

COPY build_cache/ /

RUN pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagster-postgres \
    -e dagster-k8s \
    -e dagster-aws \
    -e dagit