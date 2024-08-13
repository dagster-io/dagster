import pytest
from dagster import AutoMaterializePolicy, AutoMaterializeRule
from dagster._check import ParameterCheckError
from dagster._core.definitions.auto_materialize_rule_impls import WaitingOnAssetsRuleEvaluationData

from ...scenario_utils.asset_daemon_scenario import AssetDaemonScenario, AssetRuleEvaluationSpec
from ...scenario_utils.base_scenario import run_request
from ...scenario_utils.scenario_specs import (
    daily_partitions_def,
    dynamic_partitions_def,
    hour_partition_key,
    hourly_partitions_def,
    one_asset,
    one_asset_depends_on_two,
    three_assets_not_subsettable,
    time_partitions_start_str,
    two_partitions_def,
)


def get_cron_policy(
    cron_schedule: str,
    cron_timezone: str = "UTC",
    all_partitions: bool = False,
    max_materializations_per_minute: int = 1,
    use_cron_skip_rule: bool = False,
):
    return AutoMaterializePolicy(
        rules={
            AutoMaterializeRule.materialize_on_cron(cron_schedule, cron_timezone, all_partitions),
            AutoMaterializeRule.skip_on_not_all_parents_updated_since_cron(
                cron_schedule, cron_timezone
            )
            if use_cron_skip_rule
            else AutoMaterializeRule.skip_on_not_all_parents_updated(),
        },
        max_materializations_per_minute=max_materializations_per_minute,
    )


basic_hourly_cron_schedule = "0 * * * *"
basic_hourly_cron_rule = AutoMaterializeRule.materialize_on_cron(
    cron_schedule=basic_hourly_cron_schedule, timezone="UTC"
)

cron_scenarios = [
    AssetDaemonScenario(
        id="basic_hourly_cron_unpartitioned",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule)
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A"]))
        .assert_evaluation("A", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)])
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # still no runs should be requested
        .with_current_time_advanced(minutes=50)
        .evaluate_tick()
        .assert_requested_runs()
        # moved to a new cron schedule tick, request another run
        .with_current_time_advanced(minutes=10)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A"]))
        .assert_evaluation("A", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)])
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="basic_hourly_cron_unpartitioned_rule_added_later",
        initial_spec=one_asset.with_asset_properties(
            # this policy will never materialize the asset
            auto_materialize_policy=AutoMaterializePolicy(
                rules={AutoMaterializeRule.skip_on_parent_missing()}
            )
        ).with_current_time("2023-11-11T11:11"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        # rule added after the first tick, should capture that this asset was not materialized
        # since the previous tick
        .with_asset_properties(auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule))
        .evaluate_tick()
        .assert_requested_runs(run_request(["A"]))
        .with_not_started_runs()
        # back to the original policy which never materializes
        .with_current_time_advanced(seconds=30)
        .with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy(
                rules={AutoMaterializeRule.skip_on_parent_missing()}
            )
        )
        .evaluate_tick()
        .assert_requested_runs()
        # now we add the policy back in, but it's already been materialized since the previous tick
        # so it shouldn't execute again
        .with_current_time_advanced(seconds=30)
        .with_asset_properties(auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="basic_hourly_cron_unpartitioned_multi_asset",
        initial_spec=three_assets_not_subsettable.with_asset_properties(
            auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule)
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="basic_hourly_cron_partitioned",
        initial_spec=one_asset.with_asset_properties(
            partitions_def=hourly_partitions_def,
            auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule),
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=1, minutes=5),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A"], hour_partition_key(state.current_time)))
        .assert_evaluation(
            "A",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule, [hour_partition_key(state.current_time)]
                )
            ],
        )
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # still no runs should be requested
        .with_current_time_advanced(minutes=50)
        .evaluate_tick()
        .assert_requested_runs()
        # moved to a new cron schedule tick, request another run for the new partition
        .with_current_time_advanced(minutes=10)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A"], hour_partition_key(state.current_time, 1))),
    ),
    AssetDaemonScenario(
        id="basic_hourly_cron_partitioned_with_timezone",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=get_cron_policy("@daily", cron_timezone="America/Los_Angeles"),
            partitions_def=daily_partitions_def,
        ).with_current_time("2020-01-02T12:00"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A"], partition_key="2020-01-01"))
        .with_current_time("2020-01-03T01:00")
        .evaluate_tick()
        # it's still 2020-01-02 in America/Los_Angeles
        .assert_requested_runs()
        .with_current_time("2020-01-03T05:00")
        .evaluate_tick()
        # still 2020-01-02
        .assert_requested_runs()
        .with_current_time("2020-01-03T08:01")
        .evaluate_tick()
        # now it's 2020-01-03 (crossover happens at 8AM UTC)
        .assert_requested_runs(run_request(["A"], partition_key="2020-01-02")),
    ),
    AssetDaemonScenario(
        id="hourly_cron_unpartitioned_wait_for_parents",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            keys="C", auto_materialize_policy=get_cron_policy(basic_hourly_cron_schedule)
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        # don't materialize C because we're waiting for A and B
        .assert_requested_runs()
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(basic_hourly_cron_rule),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated()
                ).with_rule_evaluation_data(
                    WaitingOnAssetsRuleEvaluationData, waiting_on_asset_keys={"A", "B"}
                ),
            ],
            num_requested=0,
        )
        .with_runs(run_request("A"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # now just waiting on B
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(basic_hourly_cron_rule),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated()
                ).with_rule_evaluation_data(
                    WaitingOnAssetsRuleEvaluationData, waiting_on_asset_keys={"B"}
                ),
            ],
            num_requested=0,
        )
        .with_runs(run_request("B"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(run_request(["C"]))
        .assert_evaluation("C", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)])
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation("C", [])
        # even if both parents update, still on the same cron schedule tick
        .with_runs(run_request(["A", "B"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation("C", [])
        # moved to a new cron schedule tick, immediately request run
        .with_current_time_advanced(minutes=60)
        .evaluate_tick()
        .assert_requested_runs(run_request("C"))
        .assert_evaluation("C", [AssetRuleEvaluationSpec(basic_hourly_cron_rule)])
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="hourly_cron_partitioned_wait_for_parents",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            partitions_def=hourly_partitions_def,
        )
        .with_asset_properties(
            keys="C",
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule, max_materializations_per_minute=100
            ),
        )
        .with_current_time(time_partitions_start_str),
        execution_fn=lambda state: state.evaluate_tick()
        # no partitions exist yet
        .assert_requested_runs()
        .assert_evaluation("C", [])
        # don't materialize C because we're waiting for A and B
        .with_current_time_advanced(hours=1, minutes=5)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule, [hour_partition_key(state.current_time, delta=1)]
                ),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated(),
                    [hour_partition_key(state.current_time, delta=1)],
                ).with_rule_evaluation_data(
                    WaitingOnAssetsRuleEvaluationData, waiting_on_asset_keys={"A", "B"}
                ),
            ],
            num_requested=0,
        )
        .with_runs(run_request("A", hour_partition_key(state.current_time, delta=1)))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # now just waiting on B
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule, [hour_partition_key(state.current_time, delta=1)]
                ),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated(),
                    [hour_partition_key(state.current_time, delta=1)],
                ).with_rule_evaluation_data(
                    WaitingOnAssetsRuleEvaluationData, waiting_on_asset_keys={"B"}
                ),
            ],
            num_requested=0,
        )
        .with_runs(run_request("B", hour_partition_key(state.current_time, delta=1)))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(run_request("C", hour_partition_key(state.current_time, delta=1)))
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule, [hour_partition_key(state.current_time, delta=1)]
                )
            ],
        )
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation("C", [])
        # next tick happens, 2 hours later, but should still materialize both missed time partitions
        .with_current_time_advanced(hours=2)
        .with_runs(
            run_request(["A", "B"], hour_partition_key(state.current_time, delta=2)),
            run_request(["A", "B"], hour_partition_key(state.current_time, delta=3)),
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", hour_partition_key(state.current_time, delta=2)),
            run_request("C", hour_partition_key(state.current_time, delta=3)),
        )
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # now we get two new cron schedule ticks, but parents are not available for either, so we
        # keep track of both new partitions
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule,
                    [
                        # still need to materialize both of these partitions
                        hour_partition_key(state.current_time, delta=4),
                        hour_partition_key(state.current_time, delta=5),
                    ],
                ),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated(),
                    [
                        hour_partition_key(state.current_time, delta=4),
                        hour_partition_key(state.current_time, delta=5),
                    ],
                ),
            ],
        )
        # now an older set of parents become available, so we materialize the child of those parents
        .with_current_time_advanced(seconds=30)
        .with_runs(
            run_request(["A", "B"], hour_partition_key(state.current_time, delta=4)),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request("C", hour_partition_key(state.current_time, delta=4)))
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule,
                    [
                        hour_partition_key(state.current_time, delta=4),
                        hour_partition_key(state.current_time, delta=5),
                    ],
                ),
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.skip_on_not_all_parents_updated(),
                    [hour_partition_key(state.current_time, delta=5)],
                ),
            ],
        )
        # now the newer set of parents become available, so we materialize the child of those parents
        .with_current_time_advanced(seconds=30)
        .with_runs(
            run_request(["A", "B"], hour_partition_key(state.current_time, delta=5)),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request("C", hour_partition_key(state.current_time, delta=5)))
        .assert_evaluation(
            "C",
            [
                AssetRuleEvaluationSpec(
                    basic_hourly_cron_rule, [hour_partition_key(state.current_time, delta=5)]
                ),
            ],
        )
        # finally, no more runs should be requested
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation("C", []),
    ),
    AssetDaemonScenario(
        id="hourly_cron_all_partitions",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule,
                all_partitions=True,
                max_materializations_per_minute=100,
            ),
            partitions_def=hourly_partitions_def,
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=1),
        execution_fn=lambda state: state.evaluate_tick()
        .evaluate_tick()
        .assert_requested_runs(run_request(["A"], hour_partition_key(state.current_time)))
        .with_current_time_advanced(hours=2)
        .evaluate_tick()
        .assert_requested_runs(
            *[run_request(["A"], hour_partition_key(state.current_time, delta=i)) for i in range(3)]
        )
        .with_not_started_runs()
        .with_current_time_advanced(hours=2)
        .evaluate_tick()
        .assert_requested_runs(
            *[run_request(["A"], hour_partition_key(state.current_time, delta=i)) for i in range(5)]
        ),
    ),
    AssetDaemonScenario(
        id="dynamic_cron_all_partitions",
        initial_spec=one_asset.with_asset_properties(
            partitions_def=dynamic_partitions_def,
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule,
                all_partitions=True,
                max_materializations_per_minute=100,
            ),
        ),
        execution_fn=lambda state: state.with_dynamic_partitions("dynamic", ["2", "3", "4"])
        .with_current_time("2020-01-01T00:05")
        .evaluate_tick()
        .assert_requested_runs(
            run_request("A", partition_key="2"),
            run_request("A", partition_key="3"),
            run_request("A", partition_key="4"),
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_dynamic_partitions("dynamic", ["5"])
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs(
            run_request("A", partition_key="2"),
            run_request("A", partition_key="3"),
            run_request("A", partition_key="4"),
            run_request("A", partition_key="5"),
        ),
    ),
    AssetDaemonScenario(
        id="dynamic_cron_last_partition",
        initial_spec=one_asset.with_asset_properties(
            partitions_def=dynamic_partitions_def,
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule,
                max_materializations_per_minute=100,
            ),
        ),
        execution_fn=lambda state: state.with_dynamic_partitions("dynamic", ["2", "3", "4"])
        .with_current_time("2020-01-01T00:05")
        .evaluate_tick()
        .assert_requested_runs(
            run_request("A", partition_key="4"),
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_dynamic_partitions("dynamic", ["5"])
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs(
            run_request("A", partition_key="5"),
        ),
    ),
    AssetDaemonScenario(
        id="hourly_cron_unpartitioned_wait_for_parents_with_cron_skip",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            keys="C",
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule, use_cron_skip_rule=True
            ),
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        # don't materialize C because we're waiting for A and B
        .assert_requested_runs()
        .with_runs(run_request("A"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        # now just waiting on B
        .assert_requested_runs()
        .with_runs(run_request("B"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(run_request(["C"]))
        # next tick should not request any more runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .assert_evaluation("C", [])
        # even if both parents update, still on the same cron schedule tick
        .with_runs(run_request(["A", "B"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # moved to a new cron schedule tick, still do not request run, because parents have not
        # been updated since cron schedule tick
        .with_current_time_advanced(minutes=60)
        .evaluate_tick("FOO")
        .assert_requested_runs()
        .with_runs(run_request("B"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        # still waiting on A
        .assert_requested_runs()
        .with_runs(run_request("A"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        # now C can go
        .assert_requested_runs(run_request("C"))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        # no more runs
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="hourly_cron_unpartitioned_wait_for_parents_with_cron_skip_single_run",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            # all assets get this policy
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule, use_cron_skip_rule=True
            ),
        ).with_current_time("2020-01-01T00:05"),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=1)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="hourly_cron_partitioned_wait_for_parents_with_cron_skip",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            partitions_def=hourly_partitions_def,
        )
        .with_asset_properties(
            keys="C",
            auto_materialize_policy=get_cron_policy(
                basic_hourly_cron_schedule,
                max_materializations_per_minute=100,
                use_cron_skip_rule=True,
            ),
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=10),
        execution_fn=lambda state: state.evaluate_tick()
        # No runs, because we're waiting for A and B
        .assert_requested_runs()
        # A is materialized, still waiting for B
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("A", hour_partition_key(state.current_time, delta=0)))
        .evaluate_tick()
        .assert_requested_runs()
        # B is materialized, but it's an old partition, so still waiting for the correct data
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("B", hour_partition_key(state.current_time, delta=-3)))
        .evaluate_tick()
        .assert_requested_runs()
        # B is materialized with the latest partition
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("B", hour_partition_key(state.current_time, delta=0)))
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", hour_partition_key(state.current_time, delta=0)),
        )
        # no new runs the next tick
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # a new hour, no new runs until both A and B are materialized
        .with_current_time_advanced(hours=1)
        .with_runs(run_request("B", hour_partition_key(state.current_time, delta=1)))
        .evaluate_tick()
        .assert_requested_runs()
        # now A is materialized, so C kicks off
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("A", hour_partition_key(state.current_time, delta=1)))
        .evaluate_tick()
        .assert_requested_runs(
            run_request("C", hour_partition_key(state.current_time, delta=1)),
        ),
    ),
    AssetDaemonScenario(
        id="daily_unpartitioned_downstream_of_hourly_and_static_with_cron_skip",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            keys="A", partitions_def=two_partitions_def
        )
        .with_asset_properties(
            keys="B",
            partitions_def=hourly_partitions_def,
        )
        .with_asset_properties(
            keys="C",
            auto_materialize_policy=get_cron_policy(
                "0 0 * * *",  # daily
                use_cron_skip_rule=True,
            ),
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=5, minutes=1),
        execution_fn=lambda state: state.evaluate_tick()
        # No runs, because we're waiting for A and B
        .assert_requested_runs()
        # One partition of A is materialized
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("A", "1"))
        .evaluate_tick()
        .assert_requested_runs()
        # Most hours of B are materialized
        .with_current_time_advanced(seconds=30)
        .with_runs(
            *[run_request("B", hour_partition_key(state.current_time, delta=-i)) for i in range(20)]
        )
        .evaluate_tick()
        .assert_requested_runs()
        # Many hours later, other partition of B is materialized, still waiting for other
        # partitions of A
        .with_current_time_advanced(hours=15)
        .with_runs(run_request("A", "2"))
        .evaluate_tick()
        .assert_requested_runs()
        # some new partitions of B are materialized, still waiting for older ones within the time
        # window
        .with_current_time_advanced(seconds=30)
        .with_runs(
            *[
                run_request("B", hour_partition_key(state.current_time, delta=i + 1))
                for i in range(10)
            ]
        )
        .evaluate_tick()
        .assert_requested_runs()
        # remaining partitions of A are materialized, C kicks off
        .with_current_time_advanced(seconds=30)
        .with_runs(
            *[
                run_request("B", hour_partition_key(state.current_time, delta=-i))
                for i in range(20, 24)
            ]
        )
        .evaluate_tick()
        .assert_requested_runs(run_request("C"))
        # next tick, no new runs
        .with_current_time_advanced(seconds=30)
        .evaluate_tick()
        .assert_requested_runs()
        # now a new day, no new runs until both A and B are materialized
        .with_current_time_advanced(hours=10)
        .evaluate_tick()
        .assert_requested_runs()
        # all of yesterday's partitions of B are materialized, but still waiting for A
        .with_current_time_advanced(seconds=30)
        .with_runs(
            *[
                run_request("B", hour_partition_key(state.current_time, delta=i + 1))
                for i in range(10, 24)
            ]
        )
        .evaluate_tick()
        .assert_requested_runs()
        # now one partition of A is updated
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("A", "2"))
        .evaluate_tick()
        .assert_requested_runs()
        # now other partition of A is updated, C kicks off
        .with_current_time_advanced(seconds=30)
        .with_runs(run_request("A", "1"))
        .evaluate_tick()
        .assert_requested_runs(run_request("C")),
    ),
]


@pytest.mark.parametrize(
    "schedule",
    [
        "0 * * * *",
        "0 1/5 * * *",
        "0 0 1/5 * *",
        "@daily",
        "@hourly",
        "@monthly",
    ],
)
def test_valid_cron_schedules(schedule: str) -> None:
    AutoMaterializeRule.materialize_on_cron(cron_schedule=schedule)


@pytest.mark.parametrize(
    "schedule",
    [
        "0 * * * * *",
        "@something_invalid",
        "* a * * *",
        "1/1 * * *",
        "x 0 0 0 0",
    ],
)
def test_invalid_cron_schedules(schedule: str) -> None:
    with pytest.raises(ParameterCheckError, match="must be a valid cron string"):
        AutoMaterializeRule.materialize_on_cron(cron_schedule=schedule)


@pytest.mark.parametrize(
    "timezone",
    [
        "UTC",
        "America/New_York",
        "America/Argentina/Salta",
        "Europe/Vienna",
        "Europe/London",
        "Asia/Calcutta",
        "Africa/Kampala",
    ],
)
def test_valid_cron_timezones(timezone: str) -> None:
    AutoMaterializeRule.materialize_on_cron(cron_schedule="@hourly", timezone=timezone)


@pytest.mark.parametrize(
    "timezone", ["America/NotARealTimezone", "XYZ", "Foo/Bar", "America/New_York/Invalid"]
)
def test_invalid_cron_timezones(timezone: str) -> None:
    with pytest.raises(ParameterCheckError, match="must be a valid timezone"):
        AutoMaterializeRule.materialize_on_cron(cron_schedule="@hourly", timezone=timezone)
