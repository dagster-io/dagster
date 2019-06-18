# Dockerfile for Airflow

FROM dagster/buildkite-integration:py3.7.3-v4

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
	-e dagster-spark \
	-e dagster-pyspark \
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
	-e dagster-spark \
	-e dagster-pyspark \
	-e . \
	-r dagster/requirements.txt \
	-r dagster-graphql/dev-requirements.txt \
	-r dagstermill/requirements.txt \
	-r dagster-aws/requirements.txt \
	-r requirements.txt

ENTRYPOINT [ "dagster-graphql" ]

EXPOSE 3000
