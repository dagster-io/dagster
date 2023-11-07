from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule,
    DiscardOnMaxMaterializationsExceededRule,
)

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetDaemonScenarioState,
    AssetRuleEvaluationSpec,
    AssetSpecWithPartitionsDef,
    day_partition_key,
    hour_partition_key,
)
from ..base_scenario import (
    run_request,
)
from .asset_daemon_scenario_states import (
    daily_partitions_def,
    dynamic_partitions_def,
    hourly_partitions_def,
    one_asset,
    one_asset_depends_on_two,
    one_partitions_def,
    static_multipartitions_def,
    time_multipartitions_def,
    time_partitions_start,
    two_assets_in_sequence,
    two_partitions_def,
)

hourly_to_daily = AssetDaemonScenarioState(
    asset_specs=[
        AssetSpecWithPartitionsDef("A", partitions_def=hourly_partitions_def),
        AssetSpecWithPartitionsDef("B", partitions_def=daily_partitions_def, deps=["A"]),
    ]
)

partition_scenarios = [
    AssetDaemonScenario(
        id="one_asset_one_partition_never_materialized",
        initial_state=one_asset.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key="1")
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_two_partitions_never_materialized",
        initial_state=one_asset.with_asset_properties(
            partitions_def=two_partitions_def,
        ).with_all_eager(2),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key="1"),
            run_request(asset_keys=["A"], partition_key="2"),
        ),
    ),
    AssetDaemonScenario(
        id="two_assets_one_partition_never_materialized",
        initial_state=two_assets_in_sequence.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A", "B"], partition_key="1")
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_one_partition_already_requested",
        initial_state=one_asset.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["A"], partition_key="1"))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="one_asset_one_partition_already_materialized",
        initial_state=one_asset.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(asset_keys=["A"], partition_key="1"))
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="two_assets_one_partition_already_materialized",
        initial_state=two_assets_in_sequence.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.with_runs(
            run_request(asset_keys=["A", "B"], partition_key="1")
        )
        .evaluate_tick()
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="two_assets_both_upstream_partitions_materialized",
        initial_state=two_assets_in_sequence.with_asset_properties(
            partitions_def=two_partitions_def
        ).with_all_eager(2),
        execution_fn=lambda state: state.with_runs(
            run_request(asset_keys=["A"], partition_key="1"),
            run_request(asset_keys=["A"], partition_key="2"),
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(asset_keys=["B"], partition_key="1"),
            run_request(asset_keys=["B"], partition_key="2"),
        ),
    ),
    AssetDaemonScenario(
        id="parent_one_partition_one_run",
        initial_state=two_assets_in_sequence.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.with_runs(run_request(asset_keys=["A"], partition_key="1"))
        .evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["B"], partition_key="1")),
    ),
    AssetDaemonScenario(
        id="parent_rematerialized_one_partition",
        initial_state=two_assets_in_sequence.with_asset_properties(
            partitions_def=one_partitions_def
        ).with_all_eager(),
        execution_fn=lambda state: state.with_runs(
            run_request(asset_keys=["A", "B"], partition_key="1"),
            run_request(asset_keys=["A"], partition_key="1"),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request(asset_keys=["B"], partition_key="1")),
    ),
    AssetDaemonScenario(
        id="unpartitioned_to_dynamic_partitions",
        initial_state=two_assets_in_sequence.with_asset_properties(
            keys=["B"], partitions_def=dynamic_partitions_def
        ).with_all_eager(10),
        execution_fn=lambda state: state.with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs()
        .with_dynamic_partitions("dynamic", ["1"])
        .with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs(run_request("B", partition_key="1"))
        .with_dynamic_partitions("dynamic", ["2", "3", "4"])
        .with_runs(run_request("A"))
        .evaluate_tick()
        .assert_requested_runs(
            run_request("B", partition_key="1"),
            run_request("B", partition_key="2"),
            run_request("B", partition_key="3"),
            run_request("B", partition_key="4"),
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_daily_partitions_never_materialized",
        initial_state=one_asset.with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(days=2, hours=4)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key=day_partition_key(state.current_time))
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_daily_partitions_never_materialized_respect_discards",
        initial_state=one_asset.with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(days=30, hours=4)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(
            run_request(asset_keys=["A"], partition_key=day_partition_key(state.current_time))
        )
        .assert_evaluation(
            "A",
            [
                AssetRuleEvaluationSpec(
                    AutoMaterializeRule.materialize_on_missing(),
                    [day_partition_key(state.current_time, delta=-i) for i in range(30)],
                ),
                AssetRuleEvaluationSpec(
                    DiscardOnMaxMaterializationsExceededRule(limit=1),
                    [day_partition_key(state.current_time, delta=-i) for i in range(1, 30)],
                ),
            ],
            num_requested=1,
            num_discarded=29,
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_daily_partitions_two_years_never_materialized",
        initial_state=one_asset.with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(years=2, hours=4)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key=day_partition_key(state.current_time))
        ),
    ),
    AssetDaemonScenario(
        id="hourly_to_daily_partitions_never_materialized",
        initial_state=hourly_to_daily.with_current_time(time_partitions_start)
        .with_current_time_advanced(days=3, hours=1)
        .with_all_eager(100),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            *(
                run_request(
                    asset_keys=["A"], partition_key=hour_partition_key(state.current_time, delta=-i)
                )
                for i in range(24 * 3 + 1)
            )
        ),
    ),
    AssetDaemonScenario(
        id="hourly_to_daily_partitions_never_materialized2",
        initial_state=hourly_to_daily.with_current_time(time_partitions_start)
        .with_current_time_advanced(days=1, hours=4)
        .with_all_eager(100),
        execution_fn=lambda state: state.with_runs(
            *[
                run_request(
                    ["A"], partition_key=hour_partition_key(state.current_time, delta=-i - 4)
                )
                for i in range(24)
            ]
        )
        .evaluate_tick()
        .assert_requested_runs(
            *(
                run_request(
                    asset_keys=["A"], partition_key=hour_partition_key(state.current_time, delta=-i)
                )
                for i in range(4)
            ),
            run_request(asset_keys=["B"], partition_key=day_partition_key(state.current_time)),
        ),
    ),
    AssetDaemonScenario(
        id="time_dimension_multipartitioned",
        initial_state=one_asset.with_asset_properties(
            partitions_def=time_multipartitions_def,
        )
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(days=1, hours=1)
        .with_all_eager(100),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            *(
                run_request(["A"], partition_key=partition_key)
                for partition_key in time_multipartitions_def.get_multipartition_keys_with_dimension_value(
                    "time", time_partitions_start
                )
            )
        ),
    ),
    AssetDaemonScenario(
        id="static_multipartitioned",
        initial_state=one_asset.with_asset_properties(
            partitions_def=static_multipartitions_def,
        ).with_all_eager(100),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            *(
                run_request(["A"], partition_key=partition_key)
                for partition_key in static_multipartitions_def.get_partition_keys()
            )
        ),
    ),
    AssetDaemonScenario(
        id="partitioned_after_non_partitioned_multiple_updated",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            keys=["C"], partitions_def=daily_partitions_def
        )
        .with_current_time(time_partitions_start)
        .with_current_time_advanced(days=2, hours=1)
        .with_all_eager(),
        execution_fn=lambda state: state.with_runs(
            run_request(["A", "B"]),
            run_request(["C"], partition_key=day_partition_key(state.current_time)),
            run_request(["A"]),
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["C"], partition_key=day_partition_key(state.current_time))
        )
        .with_runs(run_request(["B"]))
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["C"], partition_key=day_partition_key(state.current_time))
        ),
    ),
]
