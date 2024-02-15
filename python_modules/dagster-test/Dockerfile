ARG BASE_IMAGE
ARG PYTHON_VERSION

FROM "${BASE_IMAGE}"

COPY . /

ENV GOOGLE_APPLICATION_CREDENTIALS="/modules/gac.json"

ENV DAGSTER_DISABLE_TELEMETRY=true

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

# dagster-celery specified twice to deal with pip resolution in pip 20.3.3 when only
# extras are specified
RUN pip install \
    -e modules/dagster \
    -e modules/dagster-graphql \
    -e modules/dagster-celery \
    -e modules/dagster-celery[flower,redis,kubernetes] \
    -e modules/dagster-webserver \
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
    -e modules/dagster-pipes \
    -e . \
    pyparsing\<3.0.0 \
    celery==5.2.7 \
    amqp==5.1.1 \
    flower==1.2.0 \
    grpcio==1.47.5 \
    kombu==5.2.4 \
    kubernetes==26.1.0 \
    protobuf==4.22.1 \
    redis==4.5.1 \
    SQLAlchemy==1.4.46 \
    urllib3==1.26.15

RUN ! (pip list --exclude-editable | grep -e dagster)

WORKDIR /dagster_test/test_project/

EXPOSE 80
