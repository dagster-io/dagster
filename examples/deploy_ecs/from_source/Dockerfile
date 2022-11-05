# Dagster
FROM python:3.7-slim as dagster

COPY ./python_modules/ /tmp/python_modules/


ENV DAGSTER_HOME=/opt/dagster/dagster_home/
RUN mkdir -p $DAGSTER_HOME
WORKDIR $DAGSTER_HOME
COPY dagster.yaml workspace.yaml $DAGSTER_HOME

WORKDIR /tmp

# Install:
# - dagster so we can run `dagster-daemon run`
# - dagster-aws so we can use EcsRunLauncher
# - dagster-postgres so we can use PostgresEventStorage,
#   PostgresRunStorage, and PostgresScheduleStorage
RUN pip install \
  -e python_modules/dagster \
  -e python_modules/libraries/dagster-aws \
  -e python_modules/libraries/dagster-postgres

RUN ! pip list --exclude-editable | grep -e dagster -e dagit

WORKDIR $DAGSTER_HOME

# Dagit
FROM dagster as dagit

WORKDIR /tmp

RUN pip install \
  -e python_modules/dagit \
  -e python_modules/dagster-graphql \
  -e python_modules/dagster

RUN ! pip list --exclude-editable | grep -e dagster -e dagit

WORKDIR $DAGSTER_HOME

# User Code gRPC Server
# You can either include all of your repositories in this
# stage or you can create multiple stages that each use
# the same base - one for each repository.
FROM dagster as user_code
COPY repo.py $DAGSTER_HOME
