from dagster import AutoMaterializePolicy, FreshnessPolicy
from dagster._core.definitions.asset_spec import AssetSpec

from dagster_tests.definitions_tests.declarative_automation_tests.scenario_utils.scenario_state import (
    ScenarioSpec,
)

from ...scenario_utils.asset_daemon_scenario import AssetDaemonScenario
from ...scenario_utils.base_scenario import run_request
from ...scenario_utils.scenario_specs import (
    daily_partitions_def,
    day_partition_key,
    diamond,
    one_asset,
    one_asset_depends_on_two,
    time_partitions_start_str,
    two_assets_depend_on_one,
    two_assets_in_sequence,
)

freshness_30m = FreshnessPolicy(maximum_lag_minutes=30)
freshness_60m = FreshnessPolicy(maximum_lag_minutes=60)
extended_diamond = ScenarioSpec(
    asset_specs=[*diamond.asset_specs, AssetSpec("E", deps=["C"]), AssetSpec("F", deps=["D"])]
)

freshness_policy_scenarios = [
    AssetDaemonScenario(
        id="one_asset_lazy_never_materialized",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy()
        ),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="one_asset_lazy_never_materialized_nothing_dep",
        initial_spec=ScenarioSpec(asset_specs=[AssetSpec("B", deps=["A"])]).with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(), freshness_policy=freshness_30m
        ),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(run_request("B")),
    ),
    AssetDaemonScenario(
        id="one_asset_lazy_with_freshness_policy_never_materialized",
        initial_spec=one_asset.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=FreshnessPolicy(maximum_lag_minutes=10),
        ),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(run_request("A")),
    ),
    AssetDaemonScenario(
        id="two_assets_eager_with_freshness_policies",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.eager(),
            freshness_policy=FreshnessPolicy(maximum_lag_minutes=1000),
        ),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A", "B"]))
        .with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs(run_request("B")),
    ),
    AssetDaemonScenario(
        id="one_asset_depends_on_two_lazy",
        initial_spec=one_asset_depends_on_two.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(minutes=35)
        .with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C"]))
        .with_not_started_runs()
        .evaluate_tick()
        # now policies are taken off of the root assets
        .assert_requested_runs()
        .with_asset_properties(keys=["A", "B"], auto_materialize_policy=None)
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        # waiting for A and B to become available
        .assert_requested_runs()
        .with_runs(run_request("A"))
        .evaluate_tick()
        # waiting for B to become available
        .assert_requested_runs()
        .with_runs(run_request("B"))
        .evaluate_tick()
        .assert_requested_runs(run_request("C")),
    ),
    AssetDaemonScenario(
        id="diamond_lazy_basic",
        initial_spec=diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        ),
        execution_fn=lambda state: state.evaluate_tick()
        # at first, nothing materialized, so must materialize everything
        .assert_requested_runs(run_request(["A", "B", "C", "D"]))
        .with_not_started_runs()
        # 35 minutes later, must materialize A, B, C, D again
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C", "D"]))
        # even though that run hasn't completed, it will complete within the plan window
        .with_current_time_advanced(minutes=1)
        .evaluate_tick()
        .assert_requested_runs()
        # now that run completes
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs()
        # a new run comes in
        .with_runs(run_request("A"))
        # but we don't evaluate until 35 minutes later, when it's time to materialize A, B, C, D again
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C", "D"])),
    ),
    AssetDaemonScenario(
        id="diamond_lazy_half_run_stale",
        initial_spec=diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]))
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        # the runs of A and B are too old to be used
        .assert_requested_runs(run_request(["A", "B", "C", "D"])),
    ),
    AssetDaemonScenario(
        id="diamond_lazy_half_run_and_failures",
        initial_spec=diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        ),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B"]))
        .evaluate_tick()
        .assert_requested_runs(run_request(["C", "D"]))
        .with_not_started_runs()
        # now a failed run of C comes in, nothing should happen
        .with_runs(run_request("C", fail_keys=["C"]))
        .evaluate_tick()
        .assert_requested_runs()
        # 35 minutes later assets should be materialized again
        .with_current_time_advanced(minutes=35)
        # A and C happen manually
        .with_runs(run_request(["A", "C"]))
        .with_current_time_advanced(minutes=5)
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "D"]))
        .with_not_started_runs()
        # everything was up to date, but now it's 35 minutes later, so we need to materialize again
        .with_current_time_advanced(minutes=35)
        .with_runs(run_request(["A", "B", "C"], fail_keys=["C"]))
        .evaluate_tick()
        # even though D doesn't have the most up to date data yet, we just tried to materialize C
        # and failed, so it doesn't make sense to try to run it again to get D up to date
        .assert_requested_runs()
        # now that it's been awhile since the run failed, we can try again
        .with_current_time_advanced(minutes=30)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C", "D"]))
        .with_not_started_runs()
        .with_current_time_advanced(minutes=35)
        .with_runs(
            run_request("A", fail_keys=["A"]),
        )
        .evaluate_tick()
        # need to rematerialize all, but A just failed so we don't want to retry immediately
        .assert_requested_runs()
        # now that it's been awhile since the run failed, we can try again
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C", "D"]))
        .with_not_started_runs(),
    ),
    AssetDaemonScenario(
        id="diamond_lazy_root_unselected",
        initial_spec=diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        ).with_asset_properties(keys=["A"], auto_materialize_policy=None),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B", "C", "D"]))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="extended_diamond_lazy",
        initial_spec=extended_diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
        )
        .with_asset_properties(keys=["E"], freshness_policy=freshness_30m)
        .with_asset_properties(keys=["F"], freshness_policy=freshness_60m),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "C", "E"]), run_request(["B", "D", "F"])
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(minutes=65)
        .with_runs(run_request(["A"], fail_keys=["A"]))
        .evaluate_tick()
        # need new data, but run just failed, so must wait
        .assert_requested_runs()
        .with_current_time_advanced(minutes=65)
        .evaluate_tick()
        # now we can try again
        .assert_requested_runs(run_request(["A", "B", "C", "D", "E", "F"]))
        .with_not_started_runs()
        .with_current_time_advanced(minutes=35)
        .evaluate_tick()
        # 35 minutes later, only need to refresh the assets on the shorter freshness policy
        .assert_requested_runs(run_request(["A", "C", "E"])),
    ),
    AssetDaemonScenario(
        id="two_assets_depend_on_one_lazy_with_cron_freshness",
        initial_spec=two_assets_depend_on_one.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
        )
        .with_asset_properties(keys=["B"], freshness_policy=freshness_30m)
        .with_asset_properties(
            keys=["C"],
            freshness_policy=FreshnessPolicy(cron_schedule="0 7 * * *", maximum_lag_minutes=7 * 60),
        )
        .with_current_time("2023-01-01T06:00"),
        execution_fn=lambda state: state.with_runs(run_request(["A", "B", "C"]))
        .with_current_time_advanced(minutes=90)
        .evaluate_tick()
        # A and B are stale, but C is not
        .assert_requested_runs(run_request(["A", "B"]))
        .with_not_started_runs()
        # now all are stale
        .with_current_time_advanced(hours=20)
        .evaluate_tick()
        .assert_requested_runs(run_request(["A", "B", "C"])),
    ),
    AssetDaemonScenario(
        id="extended_diamond_with_source_lazy",
        initial_spec=extended_diamond.with_asset_properties(
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
        )
        .with_asset_properties(keys=["A"], deps=["source"])
        .with_asset_properties(keys=["E"], freshness_policy=freshness_30m)
        .with_asset_properties(keys=["F"], freshness_policy=freshness_60m),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "C", "E"]), run_request(["B", "D", "F"])
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="daily_to_unpartitioned_lazy",
        initial_spec=two_assets_in_sequence.with_asset_properties(
            "A", partitions_def=daily_partitions_def
        )
        .with_asset_properties(
            "B",
            auto_materialize_policy=AutoMaterializePolicy.lazy(),
            freshness_policy=freshness_30m,
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=1),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request("A", partition_key=day_partition_key(state.current_time)))
        .evaluate_tick()
        .assert_requested_runs(run_request("B")),
    ),
]
