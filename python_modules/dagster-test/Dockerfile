ARG PYTHON_VERSION


# The tag value here must stay in sync with UNIT_IMAGE_VERSION in defines.py
FROM 968703565975.dkr.ecr.us-west-1.amazonaws.com/buildkite-unit:py${PYTHON_VERSION}-2020-11-09T183031

COPY . /

ENV GOOGLE_APPLICATION_CREDENTIALS="/modules/gac.json"

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

RUN pip install \
    -e modules/dagster \
    -e modules/dagster-graphql \
    -e modules/dagster-celery[flower,redis,kubernetes] \
    -e modules/dagster-cron \
    -e modules/dagit \
    -e modules/dagster-postgres \
    -e modules/dagster-pandas \
    -e modules/dagster-aws \
    -e modules/dagster-gcp \
    -e modules/dagster-k8s \
    -e modules/dagster-celery-k8s \
    -e modules/dagster-celery-docker \
    -e modules/dagster-airflow \
    -e .

WORKDIR /dagster_test/test_project/

EXPOSE 80
