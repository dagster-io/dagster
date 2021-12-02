# Dagster
FROM python:3.7-slim as dagster

RUN apt-get update && apt-get upgrade
RUN apt-get install git -y
ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p $DAGSTER_HOME
WORKDIR $DAGSTER_HOME
COPY dagster.yaml workspace.yaml $DAGSTER_HOME
RUN git clone https://github.com/dagster-io/dagster.git

# Install:
# - dagster so we can run `dagster-daemon run`
# - dagster-aws so we can use EcsRunLauncher
# - dagster-postgres so we can use PostgresEventStorage,
#   PostgresRunStorage, and PostgresScheduleStorage
COPY requirements-dagster.txt $DAGSTER_HOME
RUN pip install -r requirements-dagster.txt

# Dagit
FROM dagster as dagit
COPY requirements-dagit.txt $DAGSTER_HOME
RUN pip install -r requirements-dagit.txt

# User Code gRPC Server
# You can either include all of your repositories in this
# stage or you can create multiple stages that each use
# the same base - one for each repository.
FROM dagster as user_code
COPY repo.py $DAGSTER_HOME
