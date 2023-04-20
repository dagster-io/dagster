from dagster import (
    AssetKey,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionKeyRange,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    run,
    run_request,
    single_asset_run,
)

daily_partitions_def = DailyPartitionsDefinition("2013-01-05")
hourly_partitions_def = HourlyPartitionsDefinition("2013-01-05-00:00")
one_partition_partitions_def = StaticPartitionsDefinition(["a"])
two_partitions_partitions_def = StaticPartitionsDefinition(["a", "b"])
other_two_partitions_partitions_def = StaticPartitionsDefinition(["1", "2"])
time_multipartitions_def = MultiPartitionsDefinition(
    {"time": daily_partitions_def, "static": two_partitions_partitions_def}
)
static_multipartitions_def = MultiPartitionsDefinition(
    {"static_1": one_partition_partitions_def, "static_2": two_partitions_partitions_def}
)

one_asset_one_partition = [asset_def("asset1", partitions_def=one_partition_partitions_def)]
one_asset_two_partitions = [asset_def("asset1", partitions_def=two_partitions_partitions_def)]
two_assets_one_partition = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def("asset2", partitions_def=one_partition_partitions_def),
]
two_assets_in_sequence_one_partition = [
    asset_def("asset1", partitions_def=one_partition_partitions_def),
    asset_def("asset2", ["asset1"], partitions_def=one_partition_partitions_def),
]
two_assets_in_sequence_two_partitions = [
    asset_def("asset1", partitions_def=two_partitions_partitions_def),
    asset_def("asset2", ["asset1"], partitions_def=two_partitions_partitions_def),
]

one_asset_daily_partitions = [asset_def("asset1", partitions_def=daily_partitions_def)]

hourly_to_daily_partitions = [
    asset_def("hourly", partitions_def=hourly_partitions_def),
    asset_def(
        "daily",
        ["hourly"],
        partitions_def=daily_partitions_def,
    ),
]

unpartitioned_after_dynamic_asset = [
    asset_def("asset1"),
    asset_def("asset2", ["asset1"], partitions_def=DynamicPartitionsDefinition(name="foo")),
]

two_dynamic_assets = [
    asset_def("asset1", partitions_def=DynamicPartitionsDefinition(name="foo")),
    asset_def("asset2", ["asset1"], partitions_def=DynamicPartitionsDefinition(name="foo")),
]


time_multipartitioned_asset = [asset_def("asset1", partitions_def=time_multipartitions_def)]

static_multipartitioned_asset = [asset_def("asset1", partitions_def=static_multipartitions_def)]


partitioned_after_non_partitioned = [
    asset_def("asset1"),
    asset_def(
        "asset2",
        ["asset1"],
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    ),
]
non_partitioned_after_partitioned = [
    asset_def(
        "asset1",
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    ),
    asset_def("asset2", ["asset1"]),
]


partition_scenarios = {
    "one_asset_one_partition_never_materialized": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="a")],
    ),
    "one_asset_two_partitions_never_materialized": AssetReconciliationScenario(
        assets=one_asset_two_partitions,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="a"),
            run_request(asset_keys=["asset1"], partition_key="b"),
        ],
    ),
    "two_assets_one_partition_never_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1", "asset2"], partition_key="a"),
        ],
    ),
    "one_asset_one_partition_already_requested": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_one_partition, unevaluated_runs=[]
        ),
        expected_run_requests=[],
    ),
    "one_asset_one_partition_already_materialized": AssetReconciliationScenario(
        assets=one_asset_one_partition,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[],
    ),
    "two_assets_one_partition_already_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[run(["asset1", "asset2"], partition_key="a")],
        expected_run_requests=[],
    ),
    "two_assets_both_upstream_partitions_materialized": AssetReconciliationScenario(
        assets=two_assets_in_sequence_two_partitions,
        unevaluated_runs=[run(["asset1"], partition_key="a"), run(["asset1"], partition_key="b")],
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="a"),
            run_request(asset_keys=["asset2"], partition_key="b"),
        ],
    ),
    "parent_one_partition_one_run": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="a")],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
    ),
    "parent_rematerialized_one_partition": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[
            run(["asset1", "asset2"], partition_key="a"),
            single_asset_run(asset_key="asset1", partition_key="a"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
    ),
    "one_asset_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=one_asset_daily_partitions,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="2013-01-06"),
        ],
    ),
    "one_asset_daily_partitions_two_years_never_materialized": AssetReconciliationScenario(
        assets=one_asset_daily_partitions,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2015, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="2015-01-06"),
        ],
    ),
    "hourly_to_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-04:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "hourly_to_daily_partitions_never_materialized2": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[
            run(["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-00:00", end="2013-01-06-23:00")
            )
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[run_request(asset_keys=["daily"], partition_key="2013-01-06")]
        + [
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-07-00:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "hourly_to_daily_partitions_with_active_backfill_independent": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        active_backfill_targets=[
            {
                AssetKey("daily"): TimeWindowPartitionsSubset(
                    daily_partitions_def, num_partitions=1, included_partition_keys={"2013-01-06"}
                )
            },
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def,
                    num_partitions=3,
                    included_partition_keys={
                        "2013-01-06-01:00",
                        "2013-01-06-02:00",
                        "2013-01-06-03:00",
                    },
                )
            },
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-04:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "hourly_to_daily_partitions_with_active_backfill_intersecting": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        active_backfill_targets=[
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def,
                    num_partitions=3,
                    included_partition_keys={
                        "2013-01-06-04:00",
                        "2013-01-06-05:00",
                        "2013-01-06-06:00",
                    },
                )
            },
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-07:00", end="2013-01-07-03:00")
            )
        ],
    ),
    "hourly_to_daily_partitions_with_active_backfill_superceding": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        active_backfill_targets=[
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def,
                    num_partitions=len(
                        {
                            partition_key
                            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                                PartitionKeyRange(start="2013-01-06-00:00", end="2013-01-07-03:00")
                            )
                        },
                    ),
                    included_partition_keys={
                        partition_key
                        for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(start="2013-01-06-00:00", end="2013-01-07-03:00")
                        )
                    },
                )
            },
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[],
    ),
    "partial_run_partitioned": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[run(["asset1"], failed_asset_keys=["asset2"], partition_key="a")],
        expected_run_requests=[],
    ),
    "time_dimension_multipartitioned": AssetReconciliationScenario(
        assets=time_multipartitioned_asset,
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2020, month=1, day=2, hour=1),
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key=partition_key)
            for partition_key in time_multipartitions_def.get_multipartition_keys_with_dimension_value(
                "time",
                "2020-01-01",
                current_time=create_pendulum_time(year=2020, month=1, day=2, hour=1),
            )
        ],
    ),
    "static_multipartitioned": AssetReconciliationScenario(
        assets=static_multipartitioned_asset,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key=partition_key)
            for partition_key in static_multipartitions_def.get_partition_keys()
        ],
    ),
}
