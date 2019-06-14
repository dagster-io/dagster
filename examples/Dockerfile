# Dockerfile for Airflow

FROM dagster/buildkite-integration:py3.7.3-v2

RUN mkdir -p /tmp/results

WORKDIR /tmp/

ADD . . 


# Local installs must be their own invocations
# Otherwise the dev installs do not find eachother
# accurately.
RUN \
	pip install -e dagster && \
	pip install -e dagster-graphql && \
	pip install -e dagstermill && \
	pip install -e dagster-aws && \
	pip install -e dagster-spark && \
	pip install -e dagster-pyspark && \
	pip install -e .

RUN pip install \
	-r dagster/requirements.txt \
	-r dagster-graphql/dev-requirements.txt \
	-r dagstermill/requirements.txt \
	-r dagster-aws/requirements.txt \
	-r requirements.txt

ENTRYPOINT [ "dagster-graphql" ]

EXPOSE 3000
