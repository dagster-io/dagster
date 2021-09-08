import pendulum
from dagster import AssetMaterialization, Output, graph, op, repository
from dagster_test.graph_job_op_toys.log_s3 import log_s3_job
from .schedules import get_toys_schedules
from .sensors import get_toys_sensors
from dagster_test.graph_job_op_toys.asset_lineage import (
    asset_lineage_job,
    asset_lineage_partition_set,
)
from dagster_test.graph_job_op_toys.branches import branch_failed_job, branch_job
from dagster_test.graph_job_op_toys.composition import composition
from dagster_test.graph_job_op_toys.dynamic import dynamic_job
from dagster_test.graph_job_op_toys.error_monster import (
    error_monster_failing_job,
    error_monster_passing_job,
)
from dagster_test.graph_job_op_toys.hammer import hammer_default_executor_job
from dagster_test.graph_job_op_toys.log_asset import log_asset_job
from dagster_test.graph_job_op_toys.log_file import log_file_job
from dagster_test.graph_job_op_toys.log_s3 import log_s3_job
from dagster_test.graph_job_op_toys.log_spew import log_spew
from dagster_test.graph_job_op_toys.longitudinal import longitudinal_job
from dagster_test.graph_job_op_toys.many_events import many_events
from dagster_test.graph_job_op_toys.notebooks import hello_world_notebook_pipeline
from dagster_test.graph_job_op_toys.retries import retry_job
from dagster_test.graph_job_op_toys.sleepy import sleepy_job
from dagster_test.graph_job_op_toys.unreliable import unreliable_job


@op
def materialization_op():
    timestamp = pendulum.now("UTC").timestamp()
    yield AssetMaterialization(asset_key="model", metadata={"timestamp": timestamp})
    yield Output(1)


@graph
def model():
    materialization_op()


model_job = model.to_job()


@repository
def toys_repository():
    return (
        [
            composition,
            error_monster_failing_job,
            error_monster_passing_job,
            hammer_default_executor_job,
            log_asset_job,
            log_file_job,
            log_s3_job,
            log_spew,
            longitudinal_job,
            many_events,
            sleepy_job,
            retry_job,
            branch_job,
            branch_failed_job,
            unreliable_job,
            dynamic_job,
            asset_lineage_job,
            asset_lineage_partition_set,
            model_job,
            hello_world_notebook_pipeline,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )
