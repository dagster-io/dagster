FROM python:3.10-slim

RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

RUN pip install \
    dagster \
    dagster-postgres

COPY  vm_config/defs.py  /opt/dagster/app/

ENV DAGSTER_HOME=/opt/dagster/dagster_home/