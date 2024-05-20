FROM python:3.10-slim

ARG PIPELINE_DIR

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

RUN pip install \
    dagster \
    dagster-postgres

COPY ${PIPELINE_DIR}/ /opt/dagster/app/

ENV DAGSTER_HOME=/opt/dagster/dagster_home/
