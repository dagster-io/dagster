FROM dagster/buildkite-integration:py3.7.3-v3

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagster-aws dagster-aws

RUN pip install dagster/
RUN pip install dagster-graphql/
RUN pip install dagster-aws/

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT [ "dagster-graphql" ]
