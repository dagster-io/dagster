# this Dockerfile can be used to create a venv archive for PySpark on AWS EMR

FROM amazonlinux:2 AS builder

RUN yum install -y python3

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV VIRTUAL_ENV=/build/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv python install --python-preference only-managed 3.9.16 && uv python pin 3.9.16

RUN uv venv .venv

RUN uv pip install pex dagster-pipes boto3 pyspark

RUN pex dagster-pipes boto3 pyspark -o /output/venv.pex && chmod +x /output/venv.pex

# test imports
RUN /output/venv.pex -c "import dagster_pipes, pyspark, boto3;"

FROM scratch AS export

COPY --from=builder /output/venv.pex /venv.pex
