# this Dockerfile can be used to create a PEX executable for PySpark on GCP Dataproc
# it will install dagster-pipes from the current dev Dagster project

FROM bitnami/minideb AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /build

ENV VIRTUAL_ENV=/build/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG PYTHON_TAG=3.9.16-slim
RUN uv python install --python-preference only-managed 3.9.16 && uv python pin 3.9.16
RUN uv venv .venv

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install pex boto3 pyspark

COPY python_modules/dagster-pipes /build/dagster-pipes

RUN uv pip install --no-cache /build/dagster-pipes

RUN pex --include-tools /build/dagster-pipes google-cloud-storage pyspark -o /output/venv.pex && chmod +x /output/venv.pex

# test imports
RUN /output/venv.pex -c "import dagster_pipes, pyspark, google.cloud.storage;"

FROM scratch AS export

COPY --from=builder /output/venv.pex /venv.pex
