FROM python:3.7-slim

ARG DAGSTER_GIT_COMMIT

WORKDIR /tmp

# Install git
RUN apt-get update && apt-get install -yqq git

RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout ${DAGSTER_GIT_COMMIT}

WORKDIR /tmp/dagster

RUN pip install \
    -e python_modules/dagster \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-docker

ENV DAGSTER_HOME=/opt/dagster/dagster_home

RUN mkdir -p $DAGSTER_HOME

COPY dagster.yaml $DAGSTER_HOME

WORKDIR /opt/dagster/app

COPY repo.py /opt/dagster/app

EXPOSE 4000

ENTRYPOINT ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "repo.py"]