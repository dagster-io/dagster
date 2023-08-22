import datetime
from typing import Sequence

from dagster import (
    AssetsDefinition,
    PartitionKeyRange,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule,
    AutoMaterializeRuleEvaluation,
    DiscardOnMaxMaterializationsExceededRule,
    ParentUpdatedRuleEvaluationData,
    WaitingOnAssetsRuleEvaluationData,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._seven.compat.pendulum import create_pendulum_time

from ..base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    asset_def,
    run,
    run_request,
    single_asset_run,
)
from .basic_scenarios import diamond
from .freshness_policy_scenarios import (
    daily_to_unpartitioned,
    overlapping_freshness_inf,
)
from .partition_scenarios import (
    hourly_partitions_def,
    hourly_to_daily_partitions,
    two_assets_in_sequence_one_partition,
    two_partitions_partitions_def,
)

lazy_assets_nothing_dep = [
    asset_def("asset1"),
    asset_def(
        "asset2", ["asset1", "missing_source"], auto_materialize_policy=AutoMaterializePolicy.lazy()
    ),
    asset_def(
        "asset3",
        ["asset2"],
        auto_materialize_policy=AutoMaterializePolicy.lazy(),
        freshness_policy=FreshnessPolicy(maximum_lag_minutes=60),
    ),
]
single_lazy_asset = [asset_def("asset1", auto_materialize_policy=AutoMaterializePolicy.lazy())]
single_lazy_asset_with_freshness_policy = [
    asset_def(
        "asset1",
        auto_materialize_policy=AutoMaterializePolicy.lazy(),
        freshness_policy=FreshnessPolicy(maximum_lag_minutes=60),
    )
]
lopsided_vee = [
    asset_def("root1"),
    asset_def("root2"),
    asset_def("A", ["root1"]),
    asset_def("B", ["A"]),
    asset_def("C", ["B"], auto_materialize_policy=AutoMaterializePolicy.eager()),
    asset_def("D", ["root2", "C"], auto_materialize_policy=AutoMaterializePolicy.eager()),
]

time_partitioned_eager_after_non_partitioned = [
    asset_def("unpartitioned_root_a"),
    asset_def("unpartitioned_root_b"),
    asset_def(
        "time_partitioned",
        ["unpartitioned_root_a"],
        partitions_def=hourly_partitions_def,
        auto_materialize_policy=AutoMaterializePolicy.eager(),
    ),
    asset_def(
        "unpartitioned_downstream",
        ["time_partitioned", "unpartitioned_root_b"],
        auto_materialize_policy=AutoMaterializePolicy.eager(),
    ),
]
static_partitioned_eager_after_non_partitioned = [
    asset_def("unpartitioned"),
    asset_def(
        "static_partitioned",
        ["unpartitioned"],
        partitions_def=two_partitions_partitions_def,
        auto_materialize_policy=AutoMaterializePolicy.eager(max_materializations_per_minute=2),
    ),
]

non_auto_to_lazy = [
    asset_def("non_auto"),
    asset_def(
        "auto",
        ["non_auto"],
        auto_materialize_policy=AutoMaterializePolicy.lazy(),
        freshness_policy=FreshnessPolicy(maximum_lag_minutes=60),
    ),
]


def with_auto_materialize_policy(
    assets_defs: Sequence[AssetsDefinition], auto_materialize_policy: AutoMaterializePolicy
) -> Sequence[AssetsDefinition]:
    """Note: this should be implemented in core dagster at some point, and this implementation is
    a lazy hack.
    """
    ret = []
    for assets_def in assets_defs:
        ret.append(assets_def.with_attributes(auto_materialize_policy=auto_materialize_policy))
    return ret


# auto materialization policies
auto_materialize_policy_scenarios = {
    "auto_materialize_policy_lazy_missing": AssetReconciliationScenario(
        assets=single_lazy_asset,
        unevaluated_runs=[],
        expected_run_requests=[],
    ),
    "auto_materialize_policy_lazy_freshness_missing": AssetReconciliationScenario(
        assets=single_lazy_asset_with_freshness_policy,
        unevaluated_runs=[],
        expected_run_requests=[run_request(asset_keys=["asset1"])],
    ),
    "auto_materialize_policy_eager_with_freshness_policies": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            overlapping_freshness_inf, AutoMaterializePolicy.eager()
        ),
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[
            run_request(asset_keys=["asset2", "asset3", "asset4", "asset5", "asset6"])
        ],
    ),
    "auto_materialize_policy_lazy_with_freshness_policies": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            overlapping_freshness_inf, AutoMaterializePolicy.lazy()
        ),
        cursor_from=AssetReconciliationScenario(
            assets=overlapping_freshness_inf,
            unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4", "asset5", "asset6"])],
        ),
        # change at the top, should be immediately propagated as all assets have eager reconciliation
        unevaluated_runs=[run(["asset1"])],
        expected_run_requests=[],
    ),
    "auto_materialize_policy_with_default_scope_hourly_to_daily_partitions_never_materialized": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        expected_run_requests=[
            # with default scope, only the last partition is materialized
            run_request(
                asset_keys=["hourly"],
                partition_key=hourly_partitions_def.get_last_partition_key(
                    current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4)
                ),
            )
        ],
    ),
    "auto_materialize_policy_hourly_to_daily_partitions_never_materialized": (
        AssetReconciliationScenario(
            assets=with_auto_materialize_policy(
                hourly_to_daily_partitions,
                AutoMaterializePolicy.eager(
                    max_materializations_per_minute=48,
                ),
            ),
            unevaluated_runs=[],
            current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
            expected_run_requests=[
                run_request(asset_keys=["hourly"], partition_key=partition_key)
                for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange(start="2013-01-05-04:00", end="2013-01-07-03:00")
                )
            ],
            expected_evaluations=[
                AssetEvaluationSpec(
                    asset_key="hourly",
                    rule_evaluations=[
                        (
                            AutoMaterializeRuleEvaluation(
                                AutoMaterializeRule.materialize_on_missing(),
                                evaluation_data=None,
                            ),
                            hourly_partitions_def.get_partition_keys_in_range(
                                PartitionKeyRange(start="2013-01-05-0:00", end="2013-01-07-03:00")
                            ),
                        ),
                        (
                            AutoMaterializeRuleEvaluation(
                                DiscardOnMaxMaterializationsExceededRule(limit=48),
                                evaluation_data=None,
                            ),
                            hourly_partitions_def.get_partition_keys_in_range(
                                PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-05-03:00")
                            ),
                        ),
                    ],
                    num_requested=48,
                    num_discarded=4,
                )
            ],
        )
    ),
    "auto_materialize_policy_hourly_to_daily_partitions_never_materialized2": (
        AssetReconciliationScenario(
            assets=with_auto_materialize_policy(
                hourly_to_daily_partitions,
                AutoMaterializePolicy.eager(
                    max_materializations_per_minute=48,
                ).without_rules(
                    AutoMaterializeRule.materialize_on_parent_updated(),
                ),
            ),
            unevaluated_runs=[],
            current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
            expected_run_requests=[
                run_request(asset_keys=["hourly"], partition_key=partition_key)
                for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                    PartitionKeyRange(start="2013-01-05-04:00", end="2013-01-07-03:00")
                )
            ],
        )
    ),
    "auto_materialize_policy_lazy_parent_rematerialized_one_partition": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            two_assets_in_sequence_one_partition,
            AutoMaterializePolicy.lazy(),
        ),
        unevaluated_runs=[
            run(["asset1", "asset2"], partition_key="a"),
            single_asset_run(asset_key="asset1", partition_key="a"),
        ],
        # no need to rematerialize as this is a lazy policy
        expected_run_requests=[],
    ),
    "auto_materialize_policy_lazy_with_nothing_dep_and_failure": AssetReconciliationScenario(
        assets=lazy_assets_nothing_dep,
        cursor_from=AssetReconciliationScenario(
            assets=lazy_assets_nothing_dep,
            unevaluated_runs=[run(["asset1"])],
            expected_run_requests=[run_request(asset_keys=["asset2", "asset3"])],
        ),
        unevaluated_runs=[run(["asset2", "asset3"], failed_asset_keys=["asset2", "asset3"])],
        # should not run again
        expected_run_requests=[],
    ),
    "auto_materialize_policy_max_materializations_exceeded": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(max_materializations_per_minute=1).without_rules(
                AutoMaterializeRule.materialize_on_required_for_freshness(),
            ),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=5),
        expected_run_requests=[
            run_request(["hourly"], partition_key="2013-01-05-04:00"),
        ],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="hourly",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_missing(),
                            evaluation_data=None,
                        ),
                        hourly_partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(start="2013-01-05-0:00", end="2013-01-05-04:00")
                        ),
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            DiscardOnMaxMaterializationsExceededRule(limit=1),
                            evaluation_data=None,
                        ),
                        hourly_partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-05-03:00")
                        ),
                    ),
                ],
                num_requested=1,
                num_discarded=4,
            )
        ],
    ),
    "auto_materialize_policy_max_materializations_not_exceeded": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            hourly_to_daily_partitions,
            AutoMaterializePolicy.eager(max_materializations_per_minute=5).without_rules(
                AutoMaterializeRule.materialize_on_required_for_freshness()
            ),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=5),
        expected_run_requests=[
            run_request(["hourly"], partition_key="2013-01-05-04:00"),
            run_request(["hourly"], partition_key="2013-01-05-03:00"),
            run_request(["hourly"], partition_key="2013-01-05-02:00"),
            run_request(["hourly"], partition_key="2013-01-05-01:00"),
            run_request(["hourly"], partition_key="2013-01-05-00:00"),
        ],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="hourly",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_missing(),
                            evaluation_data=None,
                        ),
                        hourly_partitions_def.get_partition_keys_in_range(
                            PartitionKeyRange(start="2013-01-05-0:00", end="2013-01-05-04:00")
                        ),
                    ),
                ],
                num_requested=5,
            )
        ],
    ),
    "auto_materialize_policy_daily_to_unpartitioned_freshness": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            daily_to_unpartitioned,
            AutoMaterializePolicy.eager(),
        ),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2020, month=2, day=7, hour=4),
        expected_run_requests=[run_request(asset_keys=["daily"], partition_key="2020-02-06")],
    ),
    "auto_materialize_policy_diamond_duplicate_conditions": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            diamond,
            AutoMaterializePolicy.eager(),
        ),
        unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"]), run(["asset1", "asset2"])],
        expected_run_requests=[run_request(asset_keys=["asset3", "asset4"])],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="asset3",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey("asset1")}),
                                will_update_asset_keys=frozenset(),
                            ),
                        ),
                        None,
                    ),
                ],
                num_requested=1,
            ),
            AssetEvaluationSpec(
                asset_key="asset4",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey("asset2")}),
                                will_update_asset_keys=frozenset({AssetKey("asset3")}),
                            ),
                        ),
                        None,
                    ),
                ],
                num_requested=1,
            ),
        ],
    ),
    "auto_materialize_policy_diamond_one_side_updated": AssetReconciliationScenario(
        assets=[
            *diamond[0:3],
            *with_auto_materialize_policy(
                diamond[-1:],
                AutoMaterializePolicy.eager(),
            ),
        ],
        asset_selection=AssetSelection.keys("asset4"),
        unevaluated_runs=[run(["asset1", "asset2", "asset3", "asset4"]), run(["asset1", "asset2"])],
        expected_run_requests=[],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="asset4",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey("asset2")}),
                                will_update_asset_keys=frozenset(),
                            ),
                        ),
                        None,
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.skip_on_parent_outdated(),
                            evaluation_data=WaitingOnAssetsRuleEvaluationData(
                                waiting_on_asset_keys=frozenset({AssetKey("asset3")})
                            ),
                        ),
                        None,
                    ),
                ],
                num_skipped=1,
            ),
        ],
    ),
    "time_partitioned_after_partitioned_upstream_missing": AssetReconciliationScenario(
        assets=time_partitioned_eager_after_non_partitioned,
        asset_selection=AssetSelection.keys("time_partitioned", "unpartitioned_downstream"),
        unevaluated_runs=[],
        current_time=create_pendulum_time(year=2013, month=1, day=6, hour=1, minute=5),
        expected_run_requests=[],
    ),
    "time_partitioned_after_partitioned_upstream_materialized": AssetReconciliationScenario(
        assets=time_partitioned_eager_after_non_partitioned,
        asset_selection=AssetSelection.keys("time_partitioned", "unpartitioned_downstream"),
        unevaluated_runs=[run(["unpartitioned_root_a"])],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=1, minute=5),
        expected_run_requests=[
            run_request(asset_keys=["time_partitioned"], partition_key="2013-01-05-00:00")
        ],
    ),
    "time_partitioned_after_partitioned_upstream_rematerialized": AssetReconciliationScenario(
        assets=time_partitioned_eager_after_non_partitioned,
        asset_selection=AssetSelection.keys("time_partitioned", "unpartitioned_downstream"),
        unevaluated_runs=[
            run(["unpartitioned_root_a"]),
            run(["time_partitioned"], partition_key="2013-01-05-00:00"),
            run(["unpartitioned_root_a"]),
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=1, minute=5),
        # the latest time partition should be rematerialized
        expected_run_requests=[
            run_request(asset_keys=["time_partitioned"], partition_key="2013-01-05-00:00")
        ],
    ),
    "time_partitioned_after_partitioned_upstream_rematerialized2": AssetReconciliationScenario(
        assets=time_partitioned_eager_after_non_partitioned,
        asset_selection=AssetSelection.keys("time_partitioned", "unpartitioned_downstream"),
        unevaluated_runs=[
            run(["unpartitioned_root_a"]),
            run(["unpartitioned_root_b"]),
            # backfill
            run(["time_partitioned"], partition_key="2013-01-05-00:00"),
            run(["time_partitioned"], partition_key="2013-01-05-01:00"),
            run(["time_partitioned"], partition_key="2013-01-05-02:00"),
            run(["unpartitioned_downstream"]),
            # new root data
            run(["unpartitioned_root_a"]),
            run(["unpartitioned_root_b"]),
            # latest time partition gets newest unpartitioned root data
            run(["time_partitioned"], partition_key="2013-01-05-02:00"),
        ],
        current_time=create_pendulum_time(year=2013, month=1, day=5, hour=3, minute=5),
        # now the unpartitioned downstream should be rematerialized with the data from
        # the latest time partition
        expected_run_requests=[run_request(["unpartitioned_downstream"])],
    ),
    "static_partitioned_after_partitioned_upstream_rematerialized": AssetReconciliationScenario(
        assets=static_partitioned_eager_after_non_partitioned,
        asset_selection=AssetSelection.keys("static_partitioned"),
        unevaluated_runs=[
            run(["unpartitioned"]),
            run(["static_partitioned"], partition_key="a"),
            run(["static_partitioned"], partition_key="b"),
            run(["unpartitioned"]),
        ],
        # do execute, as we do consider the already-materialized partitions to be invalidated
        # by the new materialization of the upstream
        expected_run_requests=[
            run_request(asset_keys=["static_partitioned"], partition_key="a"),
            run_request(asset_keys=["static_partitioned"], partition_key="b"),
        ],
    ),
    "waiting_on_parents_materialize_condition": AssetReconciliationScenario(
        assets=lopsided_vee,
        asset_selection=AssetSelection.keys("C", "D"),
        cursor_from=AssetReconciliationScenario(
            assets=lopsided_vee,
            asset_selection=AssetSelection.keys("C", "D"),
            cursor_from=AssetReconciliationScenario(
                assets=lopsided_vee,
                asset_selection=AssetSelection.keys("C", "D"),
                unevaluated_runs=[
                    run(["root1", "root2", "A", "B", "C", "D"]),
                    run(["root1", "root2"]),
                ],
                expected_run_requests=[],
                expected_evaluations=[
                    AssetEvaluationSpec(
                        asset_key="D",
                        rule_evaluations=[
                            (
                                AutoMaterializeRuleEvaluation(
                                    AutoMaterializeRule.materialize_on_parent_updated(),
                                    evaluation_data=ParentUpdatedRuleEvaluationData(
                                        updated_asset_keys=frozenset(
                                            {AssetKey("C"), AssetKey("root2")}
                                        ),
                                        will_update_asset_keys=frozenset(),
                                    ),
                                ),
                                None,
                            ),
                            # waiting on A to be materialized (pulling in the new version of root1)
                            (
                                AutoMaterializeRuleEvaluation(
                                    AutoMaterializeRule.skip_on_parent_outdated(),
                                    evaluation_data=WaitingOnAssetsRuleEvaluationData(
                                        waiting_on_asset_keys=frozenset({AssetKey("A")})
                                    ),
                                ),
                                None,
                            ),
                        ],
                        num_skipped=1,
                    ),
                ],
            ),
            unevaluated_runs=[run(["A"]), run(["root2"])],
            expected_run_requests=[],
            expected_evaluations=[
                AssetEvaluationSpec(
                    asset_key="D",
                    rule_evaluations=[
                        (
                            AutoMaterializeRuleEvaluation(
                                AutoMaterializeRule.materialize_on_parent_updated(),
                                evaluation_data=ParentUpdatedRuleEvaluationData(
                                    updated_asset_keys=frozenset(
                                        {AssetKey("C"), AssetKey("root2")}
                                    ),
                                    will_update_asset_keys=frozenset(),
                                ),
                            ),
                            None,
                        ),
                        # now waiting on B to be materialized (pulling in the new version of root1/A)
                        (
                            AutoMaterializeRuleEvaluation(
                                AutoMaterializeRule.skip_on_parent_outdated(),
                                evaluation_data=WaitingOnAssetsRuleEvaluationData(
                                    waiting_on_asset_keys=frozenset({AssetKey("B")})
                                ),
                            ),
                            None,
                        ),
                    ],
                    num_skipped=1,
                ),
            ],
        ),
        unevaluated_runs=[run(["B"])],
        expected_run_requests=[
            run_request(["C", "D"]),
        ],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="C",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey("B")}),
                                will_update_asset_keys=frozenset(),
                            ),
                        ),
                        None,
                    ),
                ],
                num_requested=1,
            ),
            AssetEvaluationSpec(
                asset_key="D",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            AutoMaterializeRule.materialize_on_parent_updated(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset({AssetKey("root2")}),
                                will_update_asset_keys=frozenset({AssetKey("C")}),
                            ),
                        ),
                        None,
                    ),
                ],
                num_requested=1,
            ),
        ],
    ),
    "no_auto_materialize_policy_to_missing_lazy": AssetReconciliationScenario(
        assets=non_auto_to_lazy,
        asset_selection=AssetSelection.keys("auto"),
        unevaluated_runs=[run(["non_auto"])],
        evaluation_delta=datetime.timedelta(minutes=55),
        expected_run_requests=[run_request(["auto"])],
    ),
    "no_auto_materialize_policy_to_lazy": AssetReconciliationScenario(
        assets=non_auto_to_lazy,
        asset_selection=AssetSelection.keys("auto"),
        unevaluated_runs=[run(["non_auto", "auto"]), run(["non_auto"])],
        between_runs_delta=datetime.timedelta(minutes=55),
        expected_run_requests=[run_request(["auto"])],
    ),
}
