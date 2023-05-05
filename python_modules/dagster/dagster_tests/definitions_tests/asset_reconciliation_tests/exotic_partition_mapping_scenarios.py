from dagster import (
    DailyPartitionsDefinition,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
)
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    run_request,
    single_asset_run,
)
from .partition_scenarios import (
    one_partition_partitions_def,
    other_two_partitions_partitions_def,
    two_partitions_partitions_def,
)

fanned_out_partitions_def = StaticPartitionsDefinition(["a_1", "a_2", "a_3"])


two_assets_in_sequence_fan_in_partitions = [
    asset_def("asset1", partitions_def=fanned_out_partitions_def),
    asset_def(
        "asset2",
        {"asset1": StaticPartitionMapping({"a_1": "a", "a_2": "a", "a_3": "a"})},
        partitions_def=one_partition_partitions_def,
    ),
]

two_assets_in_sequence_fan_out_partitions = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def(
        "asset2",
        {"asset1": StaticPartitionMapping({"a": ["a_1", "a_2", "a_3"]})},
        partitions_def=fanned_out_partitions_def,
    ),
]

one_asset_self_dependency_hourly = [
    asset_def(
        "asset1",
        partitions_def=HourlyPartitionsDefinition(start_date="2020-01-01-00:00"),
        deps={"asset1": TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]


one_asset_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        deps={"asset1": TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]

root_assets_different_partitions_same_downstream = [
    asset_def("root1", partitions_def=two_partitions_partitions_def),
    asset_def("root2", partitions_def=other_two_partitions_partitions_def),
    asset_def(
        "downstream",
        {"root1": None, "root2": StaticPartitionMapping({"1": "a", "2": "b"})},
        partitions_def=two_partitions_partitions_def,
    ),
]


exotic_partition_mapping_scenarios = {
    "fan_in_partitions_none_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a_1"),
            run_request(asset_keys=["asset1"], partition_key="a_2"),
            run_request(asset_keys=["asset1"], partition_key="a_3"),
        ],
    ),
    "fan_in_partitions_some_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
        ],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a_3"),
        ],
    ),
    "fan_in_partitions_upstream_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
            single_asset_run(asset_key="asset1", partition_key="a_3"),
        ],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a"),
        ],
    ),
    "fan_in_partitions_upstream_materialized_all_materialized_before": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_in_partitions,
        unevaluated_runs=[
            single_asset_run(asset_key="asset1", partition_key="a_1"),
            single_asset_run(asset_key="asset1", partition_key="a_2"),
            single_asset_run(asset_key="asset1", partition_key="a_3"),
        ],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_in_partitions,
            unevaluated_runs=[
                single_asset_run(asset_key="asset1", partition_key="a_1"),
                single_asset_run(asset_key="asset1", partition_key="a_2"),
                single_asset_run(asset_key="asset1", partition_key="a_3"),
                single_asset_run(asset_key="asset2", partition_key="a"),
            ],
        ),
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a"),
        ],
    ),
    "fan_out_partitions_upstream_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a_1"),
            run_request(asset_keys=["asset2"], partition_key="a_2"),
            run_request(asset_keys=["asset2"], partition_key="a_3"),
        ],
    ),
    "fan_out_partitions_upstream_materialized_all_materialized_before": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[
                single_asset_run(asset_key="asset1", partition_key="a"),
                single_asset_run(asset_key="asset2", partition_key="a_1"),
                single_asset_run(asset_key="asset2", partition_key="a_2"),
                single_asset_run(asset_key="asset2", partition_key="a_3"),
            ],
        ),
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a_1"),
            run_request(asset_keys=["asset2"], partition_key="a_2"),
            run_request(asset_keys=["asset2"], partition_key="a_3"),
        ],
    ),
    "fan_out_partitions_upstream_materialized_next_tick": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[],
        expected_run_requests=[],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        ),
    ),
    "fan_out_partitions_upstream_materialize_two_more_ticks": AssetReconciliationScenario(
        assets=two_assets_in_sequence_fan_out_partitions,
        unevaluated_runs=[],
        expected_run_requests=[],
        cursor_from=AssetReconciliationScenario(
            assets=two_assets_in_sequence_fan_out_partitions,
            unevaluated_runs=[],
            cursor_from=AssetReconciliationScenario(
                assets=two_assets_in_sequence_fan_out_partitions,
                unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
            ),
        ),
    ),
    "self_dependency_never_materialized": AssetReconciliationScenario(
        assets=one_asset_self_dependency,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="2020-01-01")],
        current_time=create_pendulum_time(year=2020, month=1, day=2, hour=4),
    ),
    "self_dependency_never_materialized_recent": AssetReconciliationScenario(
        assets=one_asset_self_dependency_hourly,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="2020-01-01-00:00")
        ],
        current_time=create_pendulum_time(year=2020, month=1, day=1, hour=4),
    ),
    "self_dependency_prior_partition_requested": AssetReconciliationScenario(
        assets=one_asset_self_dependency,
        unevaluated_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_self_dependency,
            unevaluated_runs=[],
        ),
        expected_run_requests=[],
        current_time=create_pendulum_time(year=2020, month=1, day=3, hour=4),
    ),
    "self_dependency_prior_partition_materialized": AssetReconciliationScenario(
        assets=one_asset_self_dependency,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="2020-01-01")],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_self_dependency,
            unevaluated_runs=[],
        ),
        expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="2020-01-02")],
        current_time=create_pendulum_time(year=2020, month=1, day=3, hour=4),
    ),
}
