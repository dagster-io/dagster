ARG BASE_IMAGE
ARG PYTHON_VERSION

FROM "${BASE_IMAGE}"

COPY . /

ENV GOOGLE_APPLICATION_CREDENTIALS="/modules/gac.json"

ENV DAGSTER_DISABLE_TELEMETRY=true

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

# dagster-celery specified twice to deal with pip resolution in pip 20.3.3 when only
# extras are specified
RUN pip install \
    -e modules/dagster \
    -e modules/dagster-graphql \
    -e modules/dagster-celery \
    -e modules/dagster-celery[flower,redis,kubernetes] \
    -e modules/dagit \
    -e modules/dagster-postgres \
    -e modules/dagster-pandas \
    -e modules/dagster-aws \
    -e modules/dagster-gcp \
    -e modules/dagster-k8s \
    -e modules/dagster-celery-k8s \
    -e modules/dagster-celery-docker \
    -e modules/dagster-docker \
    -e modules/dagster-airflow \
    -e modules/dagstermill \
    -e . \
    pyparsing\<3.0.0

RUN ! (pip list --exclude-editable | grep -e dagster -e dagit)

WORKDIR /dagster_test/test_project/

EXPOSE 80
