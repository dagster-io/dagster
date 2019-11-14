# This is a container with all of the requirements to execute a Dagster execution step using the
# DagsterDockerOperator.

FROM dagster/buildkite-integration:py3.7.3-v4

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagster-aws dagster-aws
ADD dagster-cron dagster-cron

RUN pip install --no-deps -e dagster -e dagster-graphql -e dagster-aws -e dagster-cron
RUN pip install -e dagster -e dagster-graphql -e dagster-aws -e dagster-cron

ADD . .

ENTRYPOINT [ "dagster-graphql" ]
