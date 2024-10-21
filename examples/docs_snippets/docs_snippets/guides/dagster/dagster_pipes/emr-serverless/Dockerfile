FROM public.ecr.aws/emr-serverless/spark/emr-7.2.0

USER root

COPY --from=ghcr.io/astral-sh/uv:0.4.7 /uv /bin/uv

ENV UV_SYSTEM_PYTHON=1 \
    UV_BREAK_SYSTEM_PACKAGES=true \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON=/usr/bin/python

WORKDIR /app

COPY python_modules/dagster-pipes ./dagster-pipes

RUN uv pip install ./dagster-pipes

# EMR Serverless will run the image as hadoop
USER hadoop:hadoop
