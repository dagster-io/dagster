from dagster import Definitions, graph, job, op
from dagster_graphql import DagsterGraphQLClient


@op
def my_op():
    return 5


@op
def ingest(x):
    return x + 5


@op
def ping_dagster_webserver():
    client = DagsterGraphQLClient(
        "dagster_webserver",
        port_number=3000,
    )
    return client._execute("{__typename}")  # noqa: SLF001


@graph
def basic():
    ingest(my_op())


@job
def test_graphql():
    ping_dagster_webserver()


the_job = basic.to_job(name="the_job")

defs = Definitions(
    jobs=[the_job, test_graphql],
)
