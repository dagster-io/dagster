FROM python:3.11-slim

EXPOSE 3030

RUN pip install poetry --no-cache-dir --disable-pip-version-check

ENV POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Install Dagster Celery Runner
COPY ./example/pyproject.toml ./example/poetry.lock /app/
RUN poetry install --no-cache

COPY . /app/dagster_celery_package
RUN pip install /app/dagster_celery_package

RUN rm /app/pyproject.toml

ENV PYTHONPATH=/app

# Copy the Celery runner
COPY example/example_code /app/example_code

CMD ["dagster", "api", "grpc", "--host", "0.0.0.0", "--port", "3030", "--python-file", "./example_code/definitions.py"]