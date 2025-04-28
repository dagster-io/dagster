ARG SPARK_VERSION=3.5.5

FROM bitnami/spark:${SPARK_VERSION}

USER root

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

RUN install_packages curl

RUN uv pip install --system dagster dagster-cloud dagster-webserver dagster-aws

RUN mkdir -p /dagster_home
ENV DAGSTER_HOME=/dagster_home

COPY dagster_code.py /src/
COPY external_scala/ /src/external_scala/

# Build the Scala JAR for Spark
WORKDIR /src/external_scala/
RUN ./gradlew build

WORKDIR /src/