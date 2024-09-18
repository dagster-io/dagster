# Backcompat test repo intended for old releases of Dagster. Does not
# use `Definitions` because it is not available in our oldest supported
# releases.

from dagster import graph, job, op, repository
from dagster_graphql import DagsterGraphQLClient


@op
def the_op():
    return 5


@op
def the_ingest_op(x):
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


# This is named __repository__ so that it has the same name as a RepositoryDefinition generated from
# a Definitions object.
@repository
def the_repo():
    return [the_job, test_graphql]
