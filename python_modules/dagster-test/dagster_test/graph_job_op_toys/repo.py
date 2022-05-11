import warnings

from dagster import ExperimentalWarning

# squelch experimental warnings since we often include experimental things in toys for development
warnings.filterwarnings("ignore", category=ExperimentalWarning)

import pendulum
from dagster_test.graph_job_op_toys.asset_lineage import (
    asset_lineage_job,
    asset_lineage_partition_set,
)
from dagster_test.graph_job_op_toys.big_honkin_asset_graph import big_honkin_asset_group
from dagster_test.graph_job_op_toys.branches import branch_failed_job, branch_job
from dagster_test.graph_job_op_toys.composition import composition_job
from dagster_test.graph_job_op_toys.cross_repo_assets import (
    downstream_asset_group1,
    downstream_asset_group2,
    upstream_asset_group,
)
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
from dagster_test.graph_job_op_toys.long_asset_keys import long_asset_keys_group
from dagster_test.graph_job_op_toys.longitudinal import longitudinal_job
from dagster_test.graph_job_op_toys.many_events import many_events, many_events_subset_job
from dagster_test.graph_job_op_toys.metadata import with_metadata
from dagster_test.graph_job_op_toys.notebooks import hello_world_notebook_pipeline
from dagster_test.graph_job_op_toys.partitioned_assets import partitioned_asset_group
from dagster_test.graph_job_op_toys.retries import retry_job
from dagster_test.graph_job_op_toys.sleepy import sleepy_job
from dagster_test.graph_job_op_toys.software_defined_assets import software_defined_assets
from dagster_test.graph_job_op_toys.unreliable import unreliable_job

from dagster import AssetMaterialization, Output, graph, op, repository

from .schedules import get_toys_schedules
from .sensors import get_toys_sensors


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
            composition_job,
            error_monster_failing_job,
            error_monster_passing_job,
            hammer_default_executor_job,
            log_asset_job,
            log_file_job,
            log_s3_job,
            log_spew,
            longitudinal_job,
            many_events,
            many_events_subset_job,
            sleepy_job,
            retry_job,
            branch_job,
            branch_failed_job,
            dynamic_job,
            asset_lineage_job,
            asset_lineage_partition_set,
            model_job,
            hello_world_notebook_pipeline,
            software_defined_assets,
            with_metadata,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )


@repository
def long_asset_keys_repository():
    return [long_asset_keys_group]


@repository
def big_honkin_assets_repository():
    return [big_honkin_asset_group]


@repository
def partitioned_asset_repository():
    return [partitioned_asset_group]


@repository
def upstream_assets_repository():
    return [upstream_asset_group]


@repository
def downstream_assets_repository1():
    return [downstream_asset_group1]


@repository
def downstream_assets_repository2():
    return [downstream_asset_group2]
