# type: ignore

# Backcompat test definitions intended for use with our oldest testest release of Dagster. Does not
# use `Definitions` because it is not available in our oldest supported releases.

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
def the_op():
    return 5


@op
def the_ingest_op(x):
    return x + 5


@graph
def the_graph():
    the_ingest_op(the_op())


the_job = the_graph.to_job(name="the_job")


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


# This is named __repository__ so that it has the same name as a RepositoryDefinition generated from
# a Definitions object.
@repository
def basic_repo():
    return [the_job, the_pipeline, test_graphql]
