# this Dockerfile can be used for ECS Pipes development

FROM python:3.11-slim

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install boto3

COPY python_modules/dagster-pipes /src/dagster-pipes

RUN pip install -e /src/dagster-pipes

WORKDIR /app
COPY examples/docs_snippets/docs_snippets/guides/dagster/dagster_pipes/ecs/task.py .
