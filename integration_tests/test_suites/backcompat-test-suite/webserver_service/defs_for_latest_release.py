# Backcompat test definitions intended for use with the latest release of Dagster. Should
# include as many unique kinds of Dagster definitions as possible.

from dagster import (
    AssetCheckResult,
    ConfigurableResource,
    DailyPartitionsDefinition,
    Definitions,
    RunRequest,
    StaticPartitionsDefinition,
    asset,
    asset_check,
    define_asset_job,
    graph,
    job,
    op,
    schedule,
    sensor,
)
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
def the_graph():
    the_ingest_op(the_op())


@job
def test_graphql():
    ping_dagster_webserver()


@asset
def the_asset():
    return 5


static_partititions_def = StaticPartitionsDefinition(["a", "b"])


@asset(partitions_def=static_partititions_def)
def the_static_partitioned_asset():
    return 5


@asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
def the_time_partitioned_asset():
    return 5


the_job = the_graph.to_job(name="the_job")


@schedule(cron_schedule="* * * * *", job=the_job)
def the_schedule():
    return RunRequest()


@sensor(job=the_job)
def the_sensor():
    return RunRequest()


the_partitioned_job = the_graph.to_job(
    name="the_partitioned_job", partitions_def=static_partititions_def
)


class TheResource(ConfigurableResource):
    foo: str


@asset
def the_resource_asset(the_resource: TheResource):
    return 5


the_asset_job = define_asset_job("the_asset_job", [the_asset])


@asset_check(asset=the_asset)
def the_asset_check():
    return AssetCheckResult(passed=True)


defs = Definitions(
    assets=[
        the_asset,
        the_static_partitioned_asset,
        the_time_partitioned_asset,
        the_resource_asset,
    ],
    asset_checks=[the_asset_check],
    jobs=[the_job, the_partitioned_job, the_asset_job, test_graphql],
    schedules=[the_schedule],
    sensors=[the_sensor],
    resources={"the_resource": TheResource(foo="foo")},
)
