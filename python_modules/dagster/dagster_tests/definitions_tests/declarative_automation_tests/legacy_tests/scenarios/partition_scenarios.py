from dagster import (
    AssetKey,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionKeyRange,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import AutoMaterializeRuleEvaluation
from dagster._core.definitions.partition import DynamicPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._time import create_datetime

from ...scenario_utils.base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    asset_def,
    run,
    run_request,
    with_auto_materialize_policy,
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


time_multipartitioned_asset = [
    asset_def(
        "asset1",
        partitions_def=time_multipartitions_def,
        auto_materialize_policy=AutoMaterializePolicy.eager(max_materializations_per_minute=2),
    )
]

static_multipartitioned_asset = [asset_def("asset1", partitions_def=static_multipartitions_def)]


partitioned_after_non_partitioned = [
    asset_def("asset1"),
    asset_def("asset2"),
    asset_def(
        "asset3",
        ["asset1", "asset2"],
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

two_hourly_to_one_daily = [
    asset_def("hourly_1", partitions_def=hourly_partitions_def),
    asset_def("hourly_2", partitions_def=hourly_partitions_def),
    asset_def(
        "daily",
        ["hourly_1", "hourly_2"],
        partitions_def=daily_partitions_def,
    ),
]

unpartitioned_with_one_parent_partitioned = [
    asset_def("asset1", partitions_def=DailyPartitionsDefinition(start_date="2020-01-01")),
    asset_def("asset2"),
    asset_def(
        "asset3",
        ["asset1", "asset2"],
    ),
]

partition_scenarios = {
    "hourly_to_daily_partitions_with_active_backfill_independent": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        active_backfill_targets=[
            {
                AssetKey("daily"): TimeWindowPartitionsSubset(
                    daily_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(["2013-01-06"])
            },
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(
                    [
                        "2013-01-06-01:00",
                        "2013-01-06-02:00",
                        "2013-01-06-03:00",
                    ]
                ),
            },
        ],
        current_time=create_datetime(year=2013, month=1, day=7, hour=4),
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
                    hourly_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(
                    [
                        "2013-01-05-00:00",
                        "2013-01-05-01:00",
                        "2013-01-05-02:00",
                    ],
                ),
            },
            [AssetKey("non_existant_asset")],  # ignored since can't be loaded
        ],
        current_time=create_datetime(year=2013, month=1, day=5, hour=17),
        expected_run_requests=[
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-03:00", end="2013-01-05-16:00")
            )
        ],
    ),
    "hourly_to_daily_partitions_with_active_backfill_superceding": AssetReconciliationScenario(
        assets=hourly_to_daily_partitions,
        unevaluated_runs=[],
        active_backfill_targets=[
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(
                    hourly_partitions_def.get_partition_keys_in_range(
                        PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-07-03:00")
                    )
                )
            }
        ],
        current_time=create_datetime(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[],
    ),
    "partial_run_partitioned": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[
            run(["asset1", "asset2"], partition_key="a"),
            run(["asset1"], failed_asset_keys=["asset2"], partition_key="a"),
        ],
        expected_run_requests=[],
    ),
    "partial_run_partitioned_with_another_attempt": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[
            run(["asset1"], failed_asset_keys=["asset2"], partition_key="a"),
            run(["asset1"], partition_key="a"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
    ),
    "test_skip_on_backfill_in_progress": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(max_materializations_per_minute=None).without_rules(
                # Remove some rules to simplify the test
                AutoMaterializeRule.skip_on_parent_outdated(),
                AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            ),
        ),
        active_backfill_targets=[
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(["2013-01-05-04:00"])
            }
        ],
        unevaluated_runs=[],
        current_time=create_datetime(year=2013, month=1, day=5, hour=5),
        expected_run_requests=[
            run_request(["hourly"], partition_key="2013-01-05-00:00"),
            run_request(["hourly"], partition_key="2013-01-05-01:00"),
            run_request(["hourly"], partition_key="2013-01-05-02:00"),
            run_request(["hourly"], partition_key="2013-01-05-03:00"),
        ],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="hourly",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                            evaluation_data=None,
                        ),
                        [
                            "2013-01-05-00:00",
                            "2013-01-05-01:00",
                            "2013-01-05-02:00",
                            "2013-01-05-03:00",
                            "2013-01-05-04:00",
                        ],
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.skip_on_backfill_in_progress().to_snapshot(),
                            evaluation_data=None,
                        ),
                        [
                            "2013-01-05-04:00",
                        ],
                    ),
                ],
                num_requested=4,
                num_skipped=1,
            ),
        ],
    ),
    "test_skip_entire_asset_on_backfill_in_progress": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(max_materializations_per_minute=None)
            .without_rules(
                # Remove some rules to simplify the test
                AutoMaterializeRule.skip_on_parent_outdated(),
                AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            )
            .with_rules(AutoMaterializeRule.skip_on_backfill_in_progress(all_partitions=True)),
        ),
        active_backfill_targets=[
            {
                AssetKey("hourly"): TimeWindowPartitionsSubset(
                    hourly_partitions_def, num_partitions=None, included_time_windows=[]
                ).with_partition_keys(["2013-01-05-04:00"])
            }
        ],
        unevaluated_runs=[],
        current_time=create_datetime(year=2013, month=1, day=5, hour=5),
        expected_run_requests=[],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="hourly",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                            evaluation_data=None,
                        ),
                        [
                            "2013-01-05-00:00",
                            "2013-01-05-01:00",
                            "2013-01-05-02:00",
                            "2013-01-05-03:00",
                            "2013-01-05-04:00",
                        ],
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.skip_on_backfill_in_progress(
                                all_partitions=True
                            ).to_snapshot(),
                            evaluation_data=None,
                        ),
                        [
                            "2013-01-05-00:00",
                            "2013-01-05-01:00",
                            "2013-01-05-02:00",
                            "2013-01-05-03:00",
                            "2013-01-05-04:00",
                        ],
                    ),
                ],
                num_requested=0,
                num_skipped=5,
            ),
        ],
    ),
}
