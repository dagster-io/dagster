FROM dagster/buildkite-integration:py3.7.3-v4

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagster-aws dagster-aws
ADD requirements.txt .

RUN pip install --no-deps -e dagster -e dagster-graphql -e dagster-aws
RUN pip install -e dagster -e dagster-graphql -e dagster-aws -r requirements.txt

ADD . .

ENTRYPOINT [ "dagster-graphql" ]
