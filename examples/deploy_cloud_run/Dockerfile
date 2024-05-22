FROM python:3.10-slim

ARG PIPELINE_DIR

RUN mkdir -p /opt/dagster/app

WORKDIR /opt/dagster/app

COPY ${PIPELINE_DIR} .

RUN pip install \
    dagster \
    dagster-postgres \
    -e .

ENV DAGSTER_HOME=/opt/dagster/app/