ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

COPY build_cache/ /
ENV VIRTUAL_ENV=/usr/local
RUN pip install -U uv
RUN uv pip install \
    -e dagster \
    -e dagster-pipes \
    -e dagster-graphql \
    -e dagster-postgres \
    -e dagster-k8s \
    -e dagster-aws \
    -e dagster-webserver
