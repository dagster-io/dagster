ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

COPY build_cache/ /
RUN pip install -U uv
RUN python -m uv pip install \
    -e dagster \
    -e dagster-pipes \
    -e dagster-graphql \
    -e dagster-postgres \
    -e dagster-k8s \
    -e dagster-celery[flower,redis,kubernetes] \
    -e dagster-celery-k8s \
    -e dagster-webserver \
    grpcio==1.57.0 # https://github.com/grpc/grpc/issues/38327