# Dockerfile for Airflow

FROM dagster/buildkite-integration:py3.7.3-v2

RUN mkdir -p /tmp/results

WORKDIR /tmp/

ADD . . 

RUN pip install \
	-r dagster/requirements.txt \
	-r dagster-graphql/dev-requirements.txt \
	-r dagstermill/requirements.txt \
	-r dagster-aws/requirements.txt \
	-r requirements.txt \
	-e dagster/ \
	-e dagster-graphql/ \
	-e dagstermill/ \
	-e dagster-aws/ \
	-e .

ENTRYPOINT [ "dagster-graphql" ]

EXPOSE 3000
