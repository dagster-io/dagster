# Dagster libraries to run both dagster-webserver and the dagster-daemon. Does not
# need to have access to any pipeline code.

FROM python:3.10-slim

COPY ./python_modules/ /tmp/python_modules/

WORKDIR /tmp

RUN pip install \
    -e python_modules/dagster \
    -e python_modules/dagster-pipes \
    -e python_modules/dagster-graphql \
    -e python_modules/dagster-webserver \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-docker

# Set $DAGSTER_HOME and copy dagster instance and workspace YAML there
ENV DAGSTER_HOME=/opt/dagster/dagster_home/

RUN mkdir -p $DAGSTER_HOME

COPY dagster.yaml workspace.yaml $DAGSTER_HOME

WORKDIR $DAGSTER_HOME
