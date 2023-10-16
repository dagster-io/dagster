from dagster import (
    AssetKey,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    PartitionKeyRange,
    StaticPartitionsDefinition,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule,
    AutoMaterializeRuleEvaluation,
    DiscardOnMaxMaterializationsExceededRule,
)
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition,
)
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._seven.compat.pendulum import create_pendulum_time

from ..base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    asset_def,
    run,
    run_request,
    single_asset_run,
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
    "one_asset_daily_partitions_never_materialized_respect_discards": AssetReconciliationScenario(
        assets=one_asset_daily_partitions,
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_daily_partitions,
            unevaluated_runs=[],
            current_time=create_pendulum_time(year=2013, month=1, day=27, hour=4),
            expected_run_requests=[
                run_request(asset_keys=["asset1"], partition_key="2013-01-27"),
            ],
            expected_evaluations=[
                AssetEvaluationSpec(
                    asset_key="asset1",
                    rule_evaluations=[
                        (
                            AutoMaterializeRuleEvaluation(
                                rule_snapshot=AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                                evaluation_data=None,
                            ),
                            {f"2013-01-{i:02}" for i in range(28)},
                        ),
                        (
                            AutoMaterializeRuleEvaluation(
                                rule_snapshot=DiscardOnMaxMaterializationsExceededRule(
                                    limit=1
                                ).to_snapshot(),
                                evaluation_data=None,
                            ),
                            {f"2013-01-{i:02}" for i in range(27)},
                        ),
                    ],
                    num_requested=1,
                    num_discarded=27,
                ),
            ],
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=27, hour=5),
        # should be no new run requests as all the prior partitions were discarded
        expected_run_requests=[],
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
                PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-05-23:00")
            )
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=6, hour=4),
        expected_run_requests=[run_request(asset_keys=["daily"], partition_key="2013-01-05")]
        + [
            run_request(asset_keys=["hourly"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-00:00", end="2013-01-06-03:00")
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
                        "2013-01-05-00:00",
                        "2013-01-05-01:00",
                        "2013-01-05-02:00",
                    },
                ),
            },
            {
                AssetKey(
                    "non_existant_asset"  # ignored since can't be loaded
                ): TimeWindowPartitionsSubset(
                    hourly_partitions_def,
                    num_partitions=1,
                    included_partition_keys={
                        "2013-01-05-00:00",
                    },
                ),
            },
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=17),
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
                    hourly_partitions_def,
                    num_partitions=len(
                        {
                            partition_key
                            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                                PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-07-03:00")
                            )
                        },
                    ),
                    included_partition_keys={
                        partition_key
                        for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-07-03:00")
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
    "partial_run_partitioned_with_another_attempt": AssetReconciliationScenario(
        assets=two_assets_in_sequence_one_partition,
        unevaluated_runs=[
            run(["asset1"], failed_asset_keys=["asset2"], partition_key="a"),
            run(["asset1"], partition_key="a"),
        ],
        expected_run_requests=[run_request(asset_keys=["asset2"], partition_key="a")],
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
    "partitioned_after_non_partitioned_multiple_updates": AssetReconciliationScenario(
        assets=partitioned_after_non_partitioned,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_after_non_partitioned,
            unevaluated_runs=[
                run(["asset1", "asset2"]),
                run(["asset3"], partition_key="2020-01-02"),
                run(["asset1"]),
            ],
            current_time=create_pendulum_time(year=2020, month=1, day=3, hour=1),
            expected_run_requests=[run(["asset3"], partition_key="2020-01-02")],
        ),
        current_time=create_pendulum_time(year=2020, month=1, day=3, hour=1),
        unevaluated_runs=[run(["asset2"])],
        expected_run_requests=[run_request(["asset3"], partition_key="2020-01-02")],
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
                    hourly_partitions_def,
                    num_partitions=1,
                    included_partition_keys={"2013-01-05-04:00"},
                )
            }
        ],
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=5),
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
                    hourly_partitions_def,
                    num_partitions=1,
                    included_partition_keys={"2013-01-05-04:00"},
                )
            }
        ],
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=5),
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
