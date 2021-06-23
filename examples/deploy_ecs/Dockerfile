# Dagster
FROM python:3.7-slim as dagster

# Install:
# - dagster so we can run `dagster-daemon run`
# - dagster-aws so we can use EcsRunLauncher
# - dagster-postgres so we can use PostgresEventStorage,
#   PostgresRunStorage, and PostgresScheduleStorage
RUN pip install \
    dagster \
    dagster-aws \
    dagster-postgres

ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p $DAGSTER_HOME
COPY dagster.yaml workspace.yaml $DAGSTER_HOME

WORKDIR $DAGSTER_HOME

# Dagit
FROM dagster as dagit
RUN pip install dagit

# Pipelines
# You can either include all of your repositories in this
# stage or you can create multiple stages that each use
# the same base - one for each repository.
FROM dagster as pipelines

WORKDIR /opt/dagster/app

COPY repo.py /opt/dagster/app
