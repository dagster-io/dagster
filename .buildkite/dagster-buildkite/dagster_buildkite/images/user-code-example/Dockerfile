ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

# All packages are hard-pinned to `dagster`, so setting the version on just `DAGSTER` will ensure
# compatible versions.
RUN pip install \
    dagster==${DAGSTER_VERSION} \
    dagster-postgres \
    dagster-aws \
    dagster-k8s \
    dagster-celery[flower,redis,kubernetes] \
    dagster-celery-k8s

# Get example pipelines
COPY build_cache/ /
