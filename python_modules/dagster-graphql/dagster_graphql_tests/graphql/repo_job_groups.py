from contextlib import contextmanager

from dagster import (
    DagsterInstance,
    Definitions,
    _check as check,
    asset,
    define_asset_job,
    job,
    op,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster_graphql.test.utils import define_out_of_process_context


@asset
def my_asset():
    pass


@op
def my_op():
    pass


@job(group_name="operational/maintenance")
def grouped_op_job():
    my_op()


@job
def ungrouped_op_job():
    my_op()


grouped_asset_job = define_asset_job(
    name="grouped_asset_job",
    selection=AssetSelection.assets(my_asset),
    group_name="analytics",
)

defs = Definitions(
    assets=[my_asset],
    jobs=[grouped_op_job, ungrouped_op_job, grouped_asset_job],
)


@contextmanager
def define_job_groups_test_out_of_process_context(instance):
    check.inst_param(instance, "instance", DagsterInstance)
    with define_out_of_process_context(__file__, "defs", instance) as context:
        yield context
