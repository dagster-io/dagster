ARG BASE_IMAGE
FROM "${BASE_IMAGE}" as build

ARG DAGSTER_VERSION

RUN apt-get update -yqq && \
    apt-get install -yqq cron

RUN pip install \
    dagster==${DAGSTER_VERSION} \
    dagster-postgres==${DAGSTER_VERSION} \
    dagster-cron==${DAGSTER_VERSION} \
    dagster-celery[flower,redis,kubernetes]==${DAGSTER_VERSION} \
    dagster-aws==${DAGSTER_VERSION} \
    dagster-k8s==${DAGSTER_VERSION} \
    dagster-celery-k8s==${DAGSTER_VERSION}

# Get example pipelines
# COPY build_cache/ /

# (25.66 MB) 
RUN rm -rf /var

# (36.08 MB) 
RUN rm -rf /root/.cache

# (12.01 MB) 
RUN rm -rf /usr/lib/python2.7

# (37.21 MB)
RUN rm -rf /usr/lib/x86_64-linux-gnu/guile

FROM "${BASE_IMAGE}"
COPY --from=build / /
