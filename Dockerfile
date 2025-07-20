FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Dagster and dependencies
RUN pip install \
    dagster \
    dagster-webserver \
    dagster-postgres \
    dagster-docker \
    loguru \
    python-dotenv

# Set up Dagster home
ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p $DAGSTER_HOME

# Copy configuration files
COPY dagster_home/dagster.yaml $DAGSTER_HOME
COPY workspace.yaml $DAGSTER_HOME

WORKDIR $DAGSTER_HOME
