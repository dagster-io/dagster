from dagster import (
    AutoMaterializePolicy,
    asset,
    Definitions,
    asset_sensor,
    define_asset_job,
    RunRequest,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.sensor_definition import SensorEvaluationContext
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.dagster_run import RunRecord


def get_default_mat_policy():
    return None
    # return AutoMaterializePolicy.eager()


@asset(
    # non_argument_deps={AssetKey("some_other_asset")},
    auto_materialize_policy=AutoMaterializePolicy.eager(),
)
def return_one():
    return 1


@asset(
    auto_materialize_policy=AutoMaterializePolicy.lazy(),
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=1.0),
)
def add_one(return_one):
    return return_one + 1


# @asset(auto_materialize_policy=get_default_mat_policy())
# def add_one(return_one):
#     return return_one + 1


# @asset(auto_materialize_policy=get_default_mat_policy())
# def add_two(add_one):
#     return add_one + 2


# @asset(
#     auto_materialize_policy=AutoMaterializePolicy.lazy(),
#     freshness_policy=FreshnessPolicy(maximum_lag_minutes=5.0),
# )
# def add_three(add_two):
#     return add_two + 3


add_one_asset_job = define_asset_job("add_one_asset_job", selection="add_one")
# whole_asset_job = define_asset_job("whole_asset_job", selection="*")


# @asset_sensor(asset_key=AssetKey("some_other_asset"), job=whole_asset_job)
# def some_other_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
#     return RunRequest(run_key=context.cursor)


@asset_sensor(asset_key=AssetKey("return_one"), job=add_one_asset_job)
def return_one_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
    return RunRequest(run_key=context.cursor)


defs = Definitions(
    # assets=[return_one, add_one, add_two, add_three],
    assets=[return_one, add_one],
    sensors=[
        # return_one_sensor,
        #  some_other_asset_sensor
    ],
)
