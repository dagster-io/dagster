# type: ignore

# This file is only loaded by old versions of dagster during backcompat testing.

from dagster import graph, op, pipeline, repository, solid
from dagster_graphql import DagsterGraphQLClient


@solid
def my_solid():
    return 5


@solid
def ingest_solid(x):
    return x + 5


@pipeline
def the_pipeline():
    ingest_solid(my_solid())


@op
def my_op():
    return 5


@op
def ingest(x):
    return x + 5


@graph
def basic():
    ingest(my_op())


@solid
def ping_dagit():
    client = DagsterGraphQLClient(
        "dagster_webserver",
        port_number=3000,
    )
    return client._execute("{__typename}")  # noqa: SLF001


@pipeline
def test_graphql():
    ping_dagit()


the_job = basic.to_job(name="the_job")


@repository
def basic_repo():
    return [the_job, the_pipeline, test_graphql]
