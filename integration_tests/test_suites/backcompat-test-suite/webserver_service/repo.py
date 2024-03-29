from dagster import Definitions, asset, graph, job, op
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
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


@asset
def foo():
    return 1


@asset
def bar(foo):
    return foo + 1


asset_job = define_asset_job("asset_job", [foo, bar])

the_job = basic.to_job(name="the_job")

defs = Definitions(
    assets=[foo, bar],
    jobs=[the_job, test_graphql, asset_job],
)
