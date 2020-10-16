# Dockerfile for Airflow

FROM python:3.7.5-slim-stretch

RUN mkdir -p /tmp/results

WORKDIR /tmp/

ADD . .


# Install all local modules at once with no deps to
# ensure local versions are installed and not public
# versions

# dagster-pandas required. See https://github.com/dagster-io/dagster/issues/1485
RUN pip install --no-deps \
	-e dagster \
	-e dagster-graphql \
	-e dagster-pandas \
	-e dagstermill \
	-e dagster-aws \
	-e dagster-aws-pyspark \
	-e dagster-spark \
	-e dagster-pyspark \
	-e dagster-postgres \
	-e dagster-cron \
	-e .

# Then install all dependencies at once so that
# pip computes dep graph in once shot and is invoked only
# once
# dagster-pandas required. See https://github.com/dagster-io/dagster/issues/1485
RUN pip install \
	-e dagster \
	-e dagster-graphql \
	-e dagster-pandas \
	-e dagstermill \
	-e dagster-aws \
	-e dagster-aws-pyspark \
	-e dagster-spark \
	-e dagster-pyspark \
	-e dagster-postgres \
	-e dagster-cron \
	-e .

# do separate install because two of the requirements files require
# pytest and you cannot specify two (compatible) deps on the same module
# in two different requirements.txt files.
# See https://github.com/pypa/pip/issues/988
RUN pip install -e .[full]

ENTRYPOINT [ "dagster-graphql" ]

EXPOSE 3000
