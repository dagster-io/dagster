ARG PYTHON_VERSION

# The tag value here must stay in sync with UNIT_IMAGE_VERSION in defines.py
FROM 968703565975.dkr.ecr.us-west-1.amazonaws.com/buildkite-unit:py${PYTHON_VERSION}-2020-07-08T231944
ADD build_cache/ /
ADD . .

ENV GOOGLE_APPLICATION_CREDENTIALS="/gac.json"

RUN pip install \
    -e dagster \
    -e dagster-graphql \
    -e dagster-celery[flower,redis,kubernetes] \
    -e dagster-cron \
    -e dagit \
    -e dagster-postgres \
    -e dagster-pandas \
    -e dagster-aws \
    -e dagster-gcp \
    -e dagster-k8s \
    -e dagster-celery-k8s \
    -e dagster-airflow \
    -e .

WORKDIR /dagster_test/test_project/

EXPOSE 80
