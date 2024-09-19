import warnings

from dagster import ExperimentalWarning
from dagster._time import get_current_timestamp

# squelch experimental warnings since we often include experimental things in toys for development
warnings.filterwarnings("ignore", category=ExperimentalWarning)

from dagster import AssetMaterialization, Output, graph, load_assets_from_modules, op, repository

from dagster_test.toys import big_honkin_asset_graph as big_honkin_asset_graph_module
from dagster_test.toys.asset_checks import get_checks_and_assets
from dagster_test.toys.asset_sensors import get_asset_sensors_repo
from dagster_test.toys.auto_materializing.large_graph import (
    auto_materialize_large_static_graph as auto_materialize_large_static_graph,
    auto_materialize_large_time_graph as auto_materialize_large_time_graph,
)
from dagster_test.toys.auto_materializing.repo_1 import (
    auto_materialize_repo_1 as auto_materialize_repo_1,
)
from dagster_test.toys.auto_materializing.repo_2 import (
    auto_materialize_repo_2 as auto_materialize_repo_2,
)
from dagster_test.toys.branches import branch_failed_job, branch_job
from dagster_test.toys.composition import composition_job
from dagster_test.toys.cross_repo_assets import (
    downstream_repo1_assets,
    downstream_repo2_assets,
    upstream_repo_assets,
)
from dagster_test.toys.dynamic import dynamic_job
from dagster_test.toys.error_monster import error_monster_failing_job, error_monster_passing_job
from dagster_test.toys.freshness_checks import get_freshness_defs_pile
from dagster_test.toys.graph_backed_assets import graph_backed_asset
from dagster_test.toys.hammer import hammer_default_executor_job
from dagster_test.toys.input_managers import df_stats_job
from dagster_test.toys.log_asset import log_asset_job
from dagster_test.toys.log_file import log_file_job
from dagster_test.toys.log_s3 import log_s3_job
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.longitudinal import longitudinal_job
from dagster_test.toys.many_events import many_events, many_events_subset_job
from dagster_test.toys.metadata import with_metadata
from dagster_test.toys.multi_inputs_outputs import multi_inputs_outputs_job
from dagster_test.toys.notebooks import hello_world_notebook_pipeline
from dagster_test.toys.nothing_input import nothing_job
from dagster_test.toys.partition_config import job_with_partition_config
from dagster_test.toys.retries import retry_job
from dagster_test.toys.run_status_sensors import (
    cross_repo_job_sensor,
    cross_repo_sensor,
    cross_repo_success_job_sensor,
    fails_job,
    fails_sensor,
    instance_success_sensor,
    return_multi_run_request_success_sensor,
    return_run_request_succeeds_sensor,
    status_job,
    succeeds_job,
    success_sensor_with_pipeline_run_reaction,
    yield_multi_run_request_success_sensor,
    yield_run_request_succeeds_sensor,
)
from dagster_test.toys.schedules import get_toys_schedules
from dagster_test.toys.sensors import get_toys_sensors
from dagster_test.toys.sleepy import sleepy_job
from dagster_test.toys.software_defined_assets import software_defined_assets
from dagster_test.toys.unreliable import unreliable_job


@op
def materialization_op():
    timestamp = get_current_timestamp()
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
            nothing_job,
            sleepy_job,
            retry_job,
            branch_job,
            branch_failed_job,
            unreliable_job,
            dynamic_job,
            model_job,
            job_with_partition_config,
            multi_inputs_outputs_job,
            hello_world_notebook_pipeline,
            *software_defined_assets,
            with_metadata,
            succeeds_job,
            return_run_request_succeeds_sensor,
            yield_run_request_succeeds_sensor,
            fails_job,
            fails_sensor,
            cross_repo_sensor,
            cross_repo_job_sensor,
            cross_repo_success_job_sensor,
            status_job,
            df_stats_job,
            yield_multi_run_request_success_sensor,
            return_multi_run_request_success_sensor,
            success_sensor_with_pipeline_run_reaction,
            instance_success_sensor,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
        + get_checks_and_assets()
        + get_freshness_defs_pile()
    )


@repository
def basic_assets_repository():
    from dagster_test.toys import basic_assets

    return [load_assets_from_modules([basic_assets]), basic_assets.basic_assets_job]


@repository
def partitioned_assets_repository():
    from dagster_test.toys import partitioned_assets

    return [
        load_assets_from_modules([partitioned_assets]),
        partitioned_assets.customers_dynamic_partitions_job,
        partitioned_assets.ints_dynamic_partitions_job_sensor,
        partitioned_assets.ints_dynamic_partitions_asset_selection_sensor,
        partitioned_assets.upstream_daily_partitioned_asset_sensor,
    ]


@repository
def column_schema_repository():
    from dagster_test.toys import column_schema

    return [load_assets_from_modules([column_schema])]


@repository
def table_metadata_repository():
    from dagster_test.toys import table_metadata

    return load_assets_from_modules([table_metadata])


@repository
def long_asset_keys_repository():
    from dagster_test.toys import long_asset_keys

    return load_assets_from_modules([long_asset_keys])


@repository
def big_honkin_assets_repository():
    return [load_assets_from_modules([big_honkin_asset_graph_module])]


@repository
def upstream_assets_repository():
    return upstream_repo_assets


@repository
def downstream_assets_repository1():
    return downstream_repo1_assets


@repository
def downstream_assets_repository2():
    return downstream_repo2_assets


@repository
def graph_backed_asset_repository():
    return [graph_backed_asset]


@repository
def assets_with_sensors_repository():
    return get_asset_sensors_repo()


@repository
def conditional_assets_repository():
    from dagster_test.toys import conditional_assets

    return load_assets_from_modules([conditional_assets])


@repository
def data_versions_repository():
    from dagster_test.toys import data_versions

    return load_assets_from_modules([data_versions])
