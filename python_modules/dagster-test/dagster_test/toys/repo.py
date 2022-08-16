import warnings

from dagster import ExperimentalWarning

# squelch experimental warnings since we often include experimental things in toys for development
warnings.filterwarnings("ignore", category=ExperimentalWarning)

import pendulum
from dagster_test.toys.asset_lineage import asset_lineage_job, asset_lineage_partition_set
from dagster_test.toys.asset_sensors import get_asset_sensors_repo
from dagster_test.toys.big_honkin_asset_graph import big_honkin_asset_group
from dagster_test.toys.branches import branch_failed_job, branch_job
from dagster_test.toys.composition import composition_job
from dagster_test.toys.conditional_assets import get_conditional_assets_repo
from dagster_test.toys.cross_repo_assets import (
    downstream_asset_group1,
    downstream_asset_group2,
    upstream_asset_group,
)
from dagster_test.toys.dynamic import dynamic_job
from dagster_test.toys.error_monster import error_monster_failing_job, error_monster_passing_job
from dagster_test.toys.graph_backed_assets import graph_backed_group
from dagster_test.toys.hammer import hammer_default_executor_job
from dagster_test.toys.input_managers import df_stats_job
from dagster_test.toys.log_asset import log_asset_job
from dagster_test.toys.log_file import log_file_job
from dagster_test.toys.log_s3 import log_s3_job
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.long_asset_keys import long_asset_keys_group
from dagster_test.toys.longitudinal import longitudinal_job
from dagster_test.toys.many_events import many_events, many_events_subset_job
from dagster_test.toys.metadata import with_metadata
from dagster_test.toys.multi_inputs_outputs import multi_inputs_outputs_job
from dagster_test.toys.notebooks import hello_world_notebook_pipeline
from dagster_test.toys.partitioned_assets import partitioned_asset_group
from dagster_test.toys.retries import retry_job
from dagster_test.toys.run_status_sensors import (
    fails_job,
    fails_sensor,
    return_multi_run_request_success_sensor,
    return_run_request_succeeds_sensor,
    status_job,
    succeeds_job,
    success_sensor_with_pipeline_run_reaction,
    yield_multi_run_request_success_sensor,
    yield_run_request_succeeds_sensor,
)
from dagster_test.toys.sleepy import sleepy_job
from dagster_test.toys.software_defined_assets import software_defined_assets
from dagster_test.toys.unreliable import unreliable_job

from dagster import AssetMaterialization, Output, graph, load_assets_from_modules, op, repository

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
            unreliable_job,
            dynamic_job,
            asset_lineage_job,
            asset_lineage_partition_set,
            model_job,
            multi_inputs_outputs_job,
            hello_world_notebook_pipeline,
            software_defined_assets,
            with_metadata,
            succeeds_job,
            return_run_request_succeeds_sensor,
            yield_run_request_succeeds_sensor,
            fails_job,
            fails_sensor,
            status_job,
            df_stats_job,
            yield_multi_run_request_success_sensor,
            return_multi_run_request_success_sensor,
            success_sensor_with_pipeline_run_reaction,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )


@repository
def asset_groups_repository():
    from . import asset_groups

    return load_assets_from_modules([asset_groups])


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


@repository
def graph_backed_asset_repository():
    return [graph_backed_group]


@repository
def assets_with_sensors_repository():
    return get_asset_sensors_repo()


@repository
def conditional_assets_repository():
    return get_conditional_assets_repo()
