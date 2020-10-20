ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

RUN apt-get update -y \
    && apt-get install -y cron git

# Last git commit in dagster that build the snapshot files
RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout 5f7e7a625175eb09319516fe395004774f38793c

# for some reason this is only failing in the 3.8 image
# RUN cd dagster && git checkout "${SNAPSHOT_GIT_HASH}"

RUN cd dagster/python_modules \
    && pip install \
    -e dagster \
    -e dagster-graphql \
    -e libraries/dagster-celery[flower,redis,kubernetes] \
    -e libraries/dagster-cron \
    -e dagit \
    -e libraries/dagster-postgres \
    -e libraries/dagster-pandas \
    -e libraries/dagster-aws \
    -e libraries/dagster-gcp \
    -e libraries/dagster-k8s \
    -e libraries/dagster-celery-k8s \
    -e libraries/dagster-airflow
