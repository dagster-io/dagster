ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

ARG DAGSTER_VERSION

COPY build_cache/ /

# All packages are hard-pinned to `dagster`, so setting the version on just `DAGSTER` will ensure
# compatible versions.
RUN pip install \
    dagit==${DAGSTER_VERSION} \
    dagster \
    dagster-aws \
    dagster-celery[flower,redis,kubernetes] \
    dagster-celery-k8s \
    dagster-graphql \
    dagster-k8s \
    dagster-postgres

COPY example_project/ /
WORKDIR /example_project
