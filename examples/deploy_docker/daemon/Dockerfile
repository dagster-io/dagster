FROM python:3.7-slim

ARG DAGSTER_GIT_COMMIT

WORKDIR /tmp

# Install git
RUN apt-get update -y && apt-get install -y git

RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout ${DAGSTER_GIT_COMMIT}

WORKDIR /tmp/dagster

RUN pip install \
    -e python_modules/dagster \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-docker

RUN mkdir -p /opt/dagster/dagster_home

ENV DAGSTER_HOME=/opt/dagster/dagster_home

RUN mkdir -p $DAGSTER_HOME

# Copy dagster instance YAML to $DAGSTER_HOME
COPY dagster.yaml $DAGSTER_HOME

WORKDIR $DAGSTER_HOME

ENTRYPOINT ["dagster-daemon", "run"]