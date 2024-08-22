import datetime

from dagster import (
    DataVersion,
    DataVersionsByPartition,
    StaticPartitionsDefinition,
    asset,
    observable_source_asset,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._time import create_datetime

from ...scenario_utils.base_scenario import AssetReconciliationScenario, run_request


@observable_source_asset(auto_observe_interval_minutes=30)
def asset1():
    return DataVersion("5")


@observable_source_asset(auto_observe_interval_minutes=30)
def asset2():
    return DataVersion("5")


@asset(
    partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
    # this is just a dummy policy, as we don't want this to actually impact the logic
    auto_materialize_policy=AutoMaterializePolicy(
        rules={AutoMaterializeRule.skip_on_parent_missing()}
    ),
)
def partitioned_dummy_asset():
    return 1


@observable_source_asset(
    auto_observe_interval_minutes=30, partitions_def=StaticPartitionsDefinition(["a", "b", "c"])
)
def partitioned_observable_source_asset():
    return DataVersionsByPartition({"b": "1", "c": "5"})


@observable_source_asset(
    auto_observe_interval_minutes=30, partitions_def=StaticPartitionsDefinition(["a", "b"])
)
def partitioned_observable_source_asset2():
    return DataVersionsByPartition({"a": "1"})


auto_observe_scenarios = {
    "auto_observe_single_asset": AssetReconciliationScenario(
        [],
        [asset1],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
    "auto_observe_partitioned": AssetReconciliationScenario(
        [],
        [partitioned_observable_source_asset],
        expected_run_requests=[run_request(asset_keys=["partitioned_observable_source_asset"])],
    ),
    "auto_observe_dont_reobserve_immediately": AssetReconciliationScenario(
        [],
        [asset1],
        cursor_from=AssetReconciliationScenario(
            [], [asset1], expected_run_requests=[run_request(asset_keys=["asset1"])]
        ),
        expected_run_requests=[],
    ),
    "auto_observe_reobserve_after_time_passes": AssetReconciliationScenario(
        [],
        [asset1],
        cursor_from=AssetReconciliationScenario(
            [],
            [asset1],
            expected_run_requests=[run_request(asset_keys=["asset1"])],
            current_time=create_datetime(2020, 1, 1),
        ),
        expected_run_requests=[run_request(asset_keys=["asset1"])],
        current_time=create_datetime(2020, 1, 1) + datetime.timedelta(minutes=35),
    ),
    "auto_observe_two_assets": AssetReconciliationScenario(
        [],
        [asset1, asset2],
        expected_run_requests=[run_request(asset_keys=["asset1", "asset2"])],
    ),
    "auto_observe_two_assets_different_code_locations": AssetReconciliationScenario(
        unevaluated_runs=[],
        assets=None,
        code_locations={"location-1": [asset1], "location-2": [asset2]},
        expected_run_requests=[
            run_request(asset_keys=["asset1"]),
            run_request(asset_keys=["asset2"]),
        ],
    ),
    "auto_observe_two_assets_different_partitions_defs": AssetReconciliationScenario(
        unevaluated_runs=[],
        assets=[partitioned_observable_source_asset, partitioned_observable_source_asset2],
        expected_run_requests=[
            run_request(asset_keys=["partitioned_observable_source_asset"]),
            run_request(asset_keys=["partitioned_observable_source_asset2"]),
        ],
    ),
    "auto_observe_unpartitioned_source_to_partitioned_asset": AssetReconciliationScenario(
        unevaluated_runs=[],
        assets=[asset1, partitioned_dummy_asset],
        expected_run_requests=[
            run_request(asset_keys=["asset1"]),
        ],
    ),
}
