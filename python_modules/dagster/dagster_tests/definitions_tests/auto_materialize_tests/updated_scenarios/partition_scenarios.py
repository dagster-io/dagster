import datetime

from dagster import (
    AssetDep,
    AutoMaterializePolicy,
    AutoMaterializeRule,
    DimensionPartitionMapping,
    IdentityPartitionMapping,
    MultiPartitionMapping,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.auto_materialize_rule import DiscardOnMaxMaterializationsExceededRule

from ..asset_daemon_scenario import (
    AssetDaemonScenario,
    AssetRuleEvaluationSpec,
    day_partition_key,
    hour_partition_key,
    multi_partition_key,
)
from ..base_scenario import (
    run_request,
)
from .asset_daemon_scenario_states import (
    daily_partitions_def,
    dynamic_partitions_def,
    hourly_partitions_def,
    hourly_to_daily,
    one_asset,
    one_asset_depends_on_two,
    one_asset_self_dependency,
    one_partitions_def,
    self_partition_mapping,
    static_multipartitions_def,
    three_assets_in_sequence,
    time_multipartitions_def,
    time_partitions_start_datetime,
    time_partitions_start_str,
    two_assets_in_sequence,
    two_assets_in_sequence_fan_in_partitions,
    two_assets_in_sequence_fan_out_partitions,
    two_partitions_def,
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
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=2, hours=4)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key=day_partition_key(state.current_time))
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_daily_partitions_never_materialized_respect_discards",
        initial_state=one_asset.with_asset_properties(partitions_def=daily_partitions_def)
        .with_current_time(time_partitions_start_str)
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
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(years=2, hours=4)
        .with_all_eager(),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            run_request(asset_keys=["A"], partition_key=day_partition_key(state.current_time))
        ),
    ),
    AssetDaemonScenario(
        id="hourly_to_daily_partitions_never_materialized",
        initial_state=hourly_to_daily.with_current_time(time_partitions_start_str)
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
        initial_state=hourly_to_daily.with_current_time(time_partitions_start_str)
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
        id="hourly_to_daily_nonexistent_partitions",
        initial_state=hourly_to_daily.with_asset_properties(
            keys=["B"], partitions_def=daily_partitions_def._replace(end_offset=1)
        )
        # allow nonexistent upstream partitions
        .with_asset_properties(
            keys=["B"],
            deps=[
                AssetDep(
                    "A",
                    partition_mapping=TimeWindowPartitionMapping(
                        allow_nonexistent_upstream_partitions=True
                    ),
                )
            ],
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=9)
        .with_all_eager(),
        execution_fn=lambda state: state.with_runs(
            *(
                run_request(
                    ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(1, 10)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["B"], partition_key=day_partition_key(state.current_time, delta=1))
        )
        .with_not_started_runs()
        .with_runs(run_request(["A"], partition_key=hour_partition_key(state.current_time)))
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["B"], partition_key=day_partition_key(state.current_time, delta=1))
        )
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs()
        # now stop allowing non-existent upstream partitions and rematerialize A
        .with_asset_properties(keys=["B"], deps=["A"])
        .with_runs(run_request(["A"], partition_key=hour_partition_key(state.current_time)))
        .evaluate_tick()
        # B cannot be materialized for this partition
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="hourly_to_daily_nonexistent_partitions_become_existent",
        initial_state=hourly_to_daily.with_asset_properties(
            keys=["B"], partitions_def=daily_partitions_def._replace(end_offset=1)
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=10)
        .with_all_eager(),
        execution_fn=lambda state: state.with_runs(
            *(
                run_request(
                    ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(1, 11)
            )
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_current_time_advanced(hours=10)
        .with_runs(
            *(
                run_request(
                    ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(11, 21)
            )
        )
        .evaluate_tick()
        .assert_requested_runs()
        # now all 24 hour partitions exist
        .with_current_time_advanced(hours=5)
        .with_runs(
            *(
                run_request(
                    ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(21, 26)
            )
        )
        .evaluate_tick()
        # this asset can now kick off
        .assert_requested_runs(
            run_request(["B"], partition_key=day_partition_key(state.current_time, delta=1))
        ),
    ),
    AssetDaemonScenario(
        id="time_dimension_multipartitioned",
        initial_state=one_asset.with_asset_properties(
            partitions_def=time_multipartitions_def,
        )
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=1, hours=1)
        .with_all_eager(100),
        execution_fn=lambda state: state.evaluate_tick().assert_requested_runs(
            *(
                run_request(["A"], partition_key=partition_key)
                for partition_key in time_multipartitions_def.get_multipartition_keys_with_dimension_value(
                    "time", time_partitions_start_str
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
        .with_current_time(time_partitions_start_str)
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
    AssetDaemonScenario(
        id="one_asset_depends_on_two_nonexistent_partitions",
        initial_state=one_asset_depends_on_two.with_asset_properties(
            partitions_def=hourly_partitions_def
        )
        .with_asset_properties(
            keys=["B"],
            partitions_def=hourly_partitions_def._replace(
                start=time_partitions_start_datetime + datetime.timedelta(hours=1)
            ),
        )
        # allow nonexistent partitions
        .with_asset_properties(
            keys=["C"],
            deps=[
                "A",
                AssetDep(
                    "B",
                    partition_mapping=TimeWindowPartitionMapping(
                        allow_nonexistent_upstream_partitions=True
                    ),
                ),
            ],
        )
        .with_all_eager(100)
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=2),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(
            # nonexistent partitions are allowed, so can materialize C with A here
            run_request(["A", "C"], partition_key=hour_partition_key(state.current_time, delta=-1)),
            run_request(["A"], partition_key=hour_partition_key(state.current_time)),
            # B only exists for the second partition, and is in a separate run from A
            run_request(["B"], partition_key=hour_partition_key(state.current_time)),
        )
        .with_not_started_runs()
        .evaluate_tick()
        # C is materialized in a separate run from B
        .assert_requested_runs(
            run_request(["C"], partition_key=hour_partition_key(state.current_time))
        )
        .with_not_started_runs()
        # now stop allowing non-existent upstream partitions and rematerialize A
        .with_asset_properties(keys=["C"], deps=["A", "B"])
        .with_runs(
            run_request(["A"], partition_key=hour_partition_key(state.current_time, delta=-1))
        )
        .evaluate_tick()
        # C cannot be materialized for this partition
        .assert_requested_runs(),
    ),
    AssetDaemonScenario(
        id="two_assets_in_sequence_fan_in_partitions",
        initial_state=two_assets_in_sequence_fan_in_partitions.with_asset_properties(
            keys=["B"], auto_materialize_policy=AutoMaterializePolicy.eager()
        ),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs()
        .with_runs(run_request(["A"], partition_key="3"))
        .evaluate_tick()
        # still waiting for partitions 1 and 2
        .assert_requested_runs()
        # now can materialize
        .with_runs(run_request(["A"], partition_key="1"), run_request(["A"], partition_key="2"))
        .evaluate_tick()
        .assert_requested_runs(run_request(["B"], partition_key="1"))
        .with_runs(
            run_request(["A"], partition_key="1"),
            run_request(["A"], partition_key="2"),
            run_request(["A"], partition_key="3"),
        )
        .assert_requested_runs(run_request(["B"], partition_key="1")),
    ),
    AssetDaemonScenario(
        id="two_assets_in_sequence_fan_out_partitions",
        initial_state=two_assets_in_sequence_fan_out_partitions.with_all_eager(100),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(run_request(["A"], partition_key="1"))
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["B"], partition_key="1"),
            run_request(["B"], partition_key="2"),
            run_request(["B"], partition_key="3"),
        )
        .with_not_started_runs()
        # parent rematerialized
        .with_runs(run_request(["A"], partition_key="1"))
        .evaluate_tick()
        .assert_requested_runs(
            run_request(["B"], partition_key="1"),
            run_request(["B"], partition_key="2"),
            run_request(["B"], partition_key="3"),
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_self_dependency",
        initial_state=one_asset_self_dependency.with_all_eager()
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(hours=2),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["A"],
                partition_key=hour_partition_key(time_partitions_start_datetime, delta=2),
            )
        )
        # first partition rematerialized, don't kick off new run
        .with_not_started_runs()
        .with_runs(
            run_request(
                ["A"], partition_key=hour_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .evaluate_tick()
        .assert_requested_runs()
        .with_not_started_runs()
        # now the start date is updated, request the new first partition key
        .with_current_time_advanced(days=5)
        .with_asset_properties(
            partitions_def=hourly_partitions_def._replace(
                start=time_partitions_start_datetime + datetime.timedelta(days=5)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["A"],
                partition_key=hour_partition_key(
                    time_partitions_start_datetime + datetime.timedelta(days=5), delta=1
                ),
            )
        ),
    ),
    AssetDaemonScenario(
        id="one_asset_self_dependency_multi_partitions_def",
        initial_state=one_asset.with_asset_properties(
            partitions_def=time_multipartitions_def,
            deps=[
                AssetDep(
                    "A",
                    partition_mapping=MultiPartitionMapping(
                        {
                            "time": DimensionPartitionMapping("time", self_partition_mapping),
                            "static": DimensionPartitionMapping(
                                "static", IdentityPartitionMapping()
                            ),
                        }
                    ),
                )
            ],
        )
        .with_all_eager(2)
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=10),
        execution_fn=lambda state: state.evaluate_tick()
        .assert_requested_runs(
            *(
                run_request(
                    ["A"],
                    partition_key=multi_partition_key(
                        time=day_partition_key(time_partitions_start_datetime, delta=1),
                        static=static,
                    ),
                )
                for static in ["1", "2"]
            ),
        )
        .with_not_started_runs()
        .evaluate_tick()
        .assert_requested_runs(
            *(
                run_request(
                    ["A"],
                    partition_key=multi_partition_key(
                        time=day_partition_key(time_partitions_start_datetime, delta=2),
                        static=static,
                    ),
                )
                for static in ["1", "2"]
            ),
        ),
    ),
    AssetDaemonScenario(
        id="three_assets_in_sequence_self_dependency_in_middle",
        initial_state=three_assets_in_sequence.with_asset_properties(
            partitions_def=daily_partitions_def
        )
        .with_asset_properties(
            keys=["B"], deps=["A", AssetDep("B", partition_mapping=self_partition_mapping)]
        )
        .with_all_eager()
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=3, hours=1),
        execution_fn=lambda state: state.with_runs(
            # materialize partitions out of order, the second one coming before the first
            run_request(
                ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=2)
            )
        )
        # B's self dependency isn't satisfied yet, so don't kick off the downstream
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=3)
            )
        )
        .with_not_started_runs()
        # now the first partition of the self-dependent asset is manually materialized, which
        # unblocks the self dependency chain
        .with_runs(
            run_request(
                ["A", "B"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["B", "C"], partition_key=day_partition_key(time_partitions_start_datetime, delta=2)
            )
        )
        .with_not_started_runs()
        # first partition of the upstream rematerialized, downstreams should be kicked off
        .with_runs(
            run_request(
                ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["B", "C"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .with_not_started_runs()
        # now B requires all parents to be updated before materializing
        .with_asset_properties(
            keys=["B"],
            auto_materialize_policy=AutoMaterializePolicy.eager().with_rules(
                AutoMaterializeRule.skip_on_not_all_parents_updated()
            ),
        )
        # don't require the self-dependent asset to be updated in order for this to fire, even when
        # the skip rule is applied
        .with_runs(
            run_request(
                ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["B", "C"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        # now old partition of B is materialized, only update the downstream, not B
        .with_not_started_runs()
        .with_runs(
            run_request(
                ["B"], partition_key=day_partition_key(time_partitions_start_datetime, delta=1)
            )
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["C"],
                partition_key=day_partition_key(time_partitions_start_datetime, delta=1),
            )
        )
        # new day's partition is filled in, should still be able to materialize the new partition
        # for the self-dep asset and downstream even though an old partition is "outdated"
        .with_not_started_runs()
        .with_runs(
            run_request(
                ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=3)
            ),
        )
        .evaluate_tick()
        .assert_requested_runs(
            run_request(
                ["B", "C"], partition_key=day_partition_key(time_partitions_start_datetime, delta=3)
            )
        ),
    ),
    AssetDaemonScenario(
        id="unpartitioned_downstream_of_asymmetric_time_assets_in_series",
        initial_state=three_assets_in_sequence.with_asset_properties(
            keys=["A"],
            partitions_def=daily_partitions_def._replace(
                start=time_partitions_start_datetime + datetime.timedelta(days=4)
            ),
        )
        .with_asset_properties(keys=["B"], partitions_def=daily_partitions_def)
        .with_all_eager()
        .with_current_time(time_partitions_start_str)
        .with_current_time_advanced(days=9),
        execution_fn=lambda state: state.with_runs(
            *(
                run_request(
                    ["A"], partition_key=day_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(5, 10)
            ),
            *(
                run_request(
                    ["B"], partition_key=day_partition_key(time_partitions_start_datetime, delta=i)
                )
                for i in range(1, 10)
            ),
        )
        .evaluate_tick()
        .assert_requested_runs(run_request("C")),
    ),
]
