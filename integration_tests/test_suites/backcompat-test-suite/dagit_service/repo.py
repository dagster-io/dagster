from dagster_graphql import DagsterGraphQLClient

from dagster import graph, job, op, repository


@op
def my_op():
    return 5


@op
def ingest(x):
    return x + 5


@op
def ping_dagit():
    client = DagsterGraphQLClient(
        "dagit",
        port_number=3000,
    )
    return client._execute("{__typename}")  # pylint: disable=protected-access


@graph
def basic():
    ingest(my_op())


@job
def test_graphql():
    ping_dagit()


the_job = basic.to_job(name="the_job")


@repository
def basic_repo():
    return [the_job, test_graphql]
