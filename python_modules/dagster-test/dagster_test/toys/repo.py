import warnings

from dagster import ExperimentalWarning

# squelch experimental warnings since we often include experimental things in toys for development
warnings.filterwarnings("ignore", category=ExperimentalWarning)

import pendulum
from dagster import (
    AssetMaterialization,
    Output,
    graph,
    load_assets_from_modules,
    op,
    repository,
)

from .auto_materializing.large_graph import (
    auto_materialize_large_static_graph as auto_materialize_large_static_graph,
    auto_materialize_large_time_graph as auto_materialize_large_time_graph,
)
from .auto_materializing.repo_1 import (
    auto_materialize_repo_1 as auto_materialize_repo_1,
)
from .auto_materializing.repo_2 import (
    auto_materialize_repo_2 as auto_materialize_repo_2,
)


@op
def materialization_op():
    timestamp = pendulum.now("UTC").timestamp()
    yield AssetMaterialization(asset_key="model", metadata={"timestamp": timestamp})
    yield Output(1)


@graph
def model():
    materialization_op()


model_job = model.to_job()


# @repository
# def toys_repository():
#     return (
#         [
#             composition_job,
#             error_monster_failing_job,
#             error_monster_passing_job,
#             hammer_default_executor_job,
#             log_asset_job,
#             log_file_job,
#             log_s3_job,
#             log_spew,
#             longitudinal_job,
#             many_events,
#             many_events_subset_job,
#             nothing_job,
#             sleepy_job,
#             retry_job,
#             branch_job,
#             branch_failed_job,
#             unreliable_job,
#             dynamic_job,
#             model_job,
#             job_with_partition_config,
#             multi_inputs_outputs_job,
#             hello_world_notebook_pipeline,
#             *software_defined_assets,
#             with_metadata,
#             succeeds_job,
#             return_run_request_succeeds_sensor,
#             yield_run_request_succeeds_sensor,
#             fails_job,
#             fails_sensor,
#             cross_repo_sensor,
#             cross_repo_job_sensor,
#             cross_repo_success_job_sensor,
#             status_job,
#             df_stats_job,
#             yield_multi_run_request_success_sensor,
#             return_multi_run_request_success_sensor,
#             success_sensor_with_pipeline_run_reaction,
#             instance_success_sensor,
#         ]
#         + get_toys_schedules()
#         + get_toys_sensors()
#         + get_checks_and_assets()
#     )


@repository
def basic_assets_repository():
    from . import basic_assets

    return [load_assets_from_modules([basic_assets]), basic_assets.basic_assets_job]


# @repository
# def partitioned_assets_repository():
#     from . import partitioned_assets

#     return [
#         load_assets_from_modules([partitioned_assets]),
#         partitioned_assets.customers_dynamic_partitions_job,
#         partitioned_assets.ints_dynamic_partitions_job_sensor,
#         partitioned_assets.ints_dynamic_partitions_asset_selection_sensor,
#         partitioned_assets.upstream_daily_partitioned_asset_sensor,
#     ]


# @repository
# def table_metadata_repository():
#     from . import table_metadata

#     return load_assets_from_modules([table_metadata])


# @repository
# def long_asset_keys_repository():
#     from . import long_asset_keys

#     return load_assets_from_modules([long_asset_keys])


# @repository
# def big_honkin_assets_repository():
#     return [load_assets_from_modules([big_honkin_asset_graph_module])]


# @repository
# def upstream_assets_repository():
#     return upstream_repo_assets


# @repository
# def downstream_assets_repository1():
#     return downstream_repo1_assets


# @repository
# def downstream_assets_repository2():
#     return downstream_repo2_assets


# @repository
# def graph_backed_asset_repository():
#     return [graph_backed_asset]


# @repository
# def assets_with_sensors_repository():
#     return get_asset_sensors_repo()


# @repository
# def conditional_assets_repository():
#     from . import conditional_assets

#     return load_assets_from_modules([conditional_assets])


# @repository
# def data_versions_repository():
#     from . import data_versions

#     return load_assets_from_modules([data_versions])
