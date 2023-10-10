from dagster import (
    DailyPartitionsDefinition,
    DimensionPartitionMapping,
    IdentityPartitionMapping,
    MultiPartitionKey,
    MultiPartitionMapping,
    MultiPartitionsDefinition,
    StaticPartitionMapping,
    StaticPartitionsDefinition,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.time_window_partitions import (
    HourlyPartitionsDefinition,
)
from dagster._seven.compat.pendulum import create_pendulum_time

from ..base_scenario import (
    AssetReconciliationScenario,
    asset_def,
    run,
    run_request,
    single_asset_run,
    with_auto_materialize_policy,
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

one_asset_self_dependency_hourly_many_partitions = [
    asset_def(
        "asset1",
        partitions_def=HourlyPartitionsDefinition(start_date="2015-01-01-00:00"),
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
one_asset_self_dependency_later_start_date = [
    asset_def(
        "asset1",
        partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
        deps={"asset1": TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)},
    )
]
three_assets_self_dependency = [
    asset_def("asset1", partitions_def=DailyPartitionsDefinition(start_date="2020-01-01")),
    asset_def(
        "asset2",
        partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
        deps={
            "asset1": TimeWindowPartitionMapping(),
            "asset2": TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
        },
    ),
    asset_def(
        "asset3", ["asset2"], partitions_def=DailyPartitionsDefinition(start_date="2020-01-01")
    ),
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

multipartitioned_self_dependency = [
    asset_def(
        "asset1",
        partitions_def=MultiPartitionsDefinition(
            {
                "time": DailyPartitionsDefinition(start_date="2020-01-01"),
                "abc": StaticPartitionsDefinition(["a", "b", "c"]),
            }
        ),
        deps={
            "asset1": MultiPartitionMapping(
                {
                    "time": DimensionPartitionMapping(
                        "time", TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
                    ),
                    "abc": DimensionPartitionMapping("abc", IdentityPartitionMapping()),
                }
            )
        },
        auto_materialize_policy=AutoMaterializePolicy.eager(max_materializations_per_minute=3),
    )
]

unpartitioned_downstream_of_asymmetric_time_assets_in_series = [
    asset_def("asset1", partitions_def=DailyPartitionsDefinition("2023-01-05")),
    asset_def("asset2", partitions_def=DailyPartitionsDefinition("2023-01-01"), deps=["asset1"]),
    asset_def("unpartitioned", partitions_def=None, deps=["asset2"]),
]

upstream_starts_later_than_downstream = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def(
        "asset2", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"), deps=["asset1"]
    ),
]

one_parent_starts_later_and_nonexistent_upstream_partitions_not_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps=["asset1", "asset2"],
    ),
]

one_parent_starts_later_and_nonexistent_upstream_partitions_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-03:00")),
    asset_def("asset2", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset3",
        partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00"),
        deps={
            "asset1": TimeWindowPartitionMapping(allow_nonexistent_upstream_partitions=True),
            "asset2": TimeWindowPartitionMapping(),
        },
    ),
]

hourly_with_daily_downstream_nonexistent_upstream_partitions_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset2",
        partitions_def=DailyPartitionsDefinition("2023-01-01", end_offset=1),
        deps={"asset1": TimeWindowPartitionMapping(allow_nonexistent_upstream_partitions=True)},
    ),
]

hourly_with_daily_downstream_nonexistent_upstream_partitions_not_allowed = [
    asset_def("asset1", partitions_def=HourlyPartitionsDefinition("2023-01-01-00:00")),
    asset_def(
        "asset2",
        partitions_def=DailyPartitionsDefinition("2023-01-01", end_offset=1),
        deps={"asset1": TimeWindowPartitionMapping(allow_nonexistent_upstream_partitions=False)},
    ),
]


exotic_partition_mapping_scenarios = {
    "self_dependency_never_materialized_many_partitions": AssetReconciliationScenario(
        assets=one_asset_self_dependency_hourly_many_partitions,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(asset_keys=["asset1"], partition_key="2015-01-01-00:00")
        ],
        current_time=create_pendulum_time(year=2015, month=4, day=1, hour=0),
    ),
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
        current_time=create_pendulum_time(year=2020, month=1, day=3, hour=4, minute=4),
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
    "self_dependency_prior_partition_rematerialized": AssetReconciliationScenario(
        assets=one_asset_self_dependency,
        # this is rematerialized
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="2020-01-01")],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_self_dependency,
            unevaluated_runs=[
                single_asset_run(asset_key="asset1", partition_key="2020-01-01"),
                single_asset_run(asset_key="asset1", partition_key="2020-01-02"),
                single_asset_run(asset_key="asset1", partition_key="2020-01-03"),
            ],
            expected_run_requests=[],
            current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
        ),
        # should not rematerialize partition because of this update
        expected_run_requests=[],
        current_time=create_pendulum_time(year=2020, month=1, day=4, hour=5),
    ),
    "self_dependency_upstream_prior_partition_materialized": AssetReconciliationScenario(
        assets=three_assets_self_dependency,
        unevaluated_runs=[
            # request from the previous tick
            run(["asset1"], partition_key="2020-01-01"),
            # now asset2 is filled in (maybe manually)
            run(["asset2"], partition_key="2020-01-01"),
        ],
        cursor_from=AssetReconciliationScenario(
            assets=three_assets_self_dependency,
            # in this case, we materialize the parents out of order (01-02 before 01-01)
            unevaluated_runs=[
                run(["asset1"], partition_key="2020-01-02"),
            ],
            expected_run_requests=[
                # asset2 cannot run in the same run as asset1 (so no 01-01), and 01-02 cannot be
                # executed without the prior day's data
                run_request(["asset1"], partition_key="2020-01-01"),
            ],
            current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
        ),
        expected_run_requests=[
            # next self-dependent partition can now be materialized with its downstream
            run_request(["asset2", "asset3"], partition_key="2020-01-02"),
        ],
        current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
    ),
    "self_dependency_upstream_prior_partition_rematerialized": AssetReconciliationScenario(
        assets=three_assets_self_dependency,
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="2020-01-01")],
        cursor_from=AssetReconciliationScenario(
            assets=three_assets_self_dependency,
            unevaluated_runs=[
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-01"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-02"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-03"),
            ],
            expected_run_requests=[],
            current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
        ),
        # should respond to an upstream asset being rematerialized
        expected_run_requests=[run_request(["asset2", "asset3"], partition_key="2020-01-01")],
        current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
    ),
    "self_dependency_upstream_prior_partition_rematerialized_with_not_all_parents_updated": AssetReconciliationScenario(
        assets=with_auto_materialize_policy(
            three_assets_self_dependency,
            AutoMaterializePolicy.eager().with_rules(
                AutoMaterializeRule.skip_on_not_all_parents_updated()
            ),
        ),
        unevaluated_runs=[single_asset_run(asset_key="asset1", partition_key="2020-01-02")],
        cursor_from=AssetReconciliationScenario(
            assets=with_auto_materialize_policy(
                three_assets_self_dependency,
                AutoMaterializePolicy.eager().with_rules(
                    AutoMaterializeRule.skip_on_not_all_parents_updated()
                ),
            ),
            unevaluated_runs=[
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-01"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-02"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-03"),
            ],
            expected_run_requests=[],
            current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
        ),
        # should respond to an upstream asset being rematerialized, even though the past time
        # partition was not updated
        expected_run_requests=[run_request(["asset2", "asset3"], partition_key="2020-01-02")],
        current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
    ),
    "self_dependency_upstream_prior_partition_outdated_ignore": AssetReconciliationScenario(
        assets=three_assets_self_dependency,
        # new day's partition filled in
        unevaluated_runs=[run(["asset1"], partition_key="2020-01-04")],
        cursor_from=AssetReconciliationScenario(
            assets=three_assets_self_dependency,
            unevaluated_runs=[
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-01"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-02"),
                run(["asset1", "asset2", "asset3"], partition_key="2020-01-03"),
                # old partition is updated
                run(["asset2"], partition_key="2020-01-02"),
            ],
            # only update the downstream, not the next daily partition
            expected_run_requests=[
                run_request(["asset3"], partition_key="2020-01-02"),
            ],
            current_time=create_pendulum_time(year=2020, month=1, day=4, hour=4),
        ),
        # should still be able to materialize the new partition for the self-dep asset (and
        # downstream), even though an old partition is "outdated"
        expected_run_requests=[run_request(["asset2", "asset3"], partition_key="2020-01-04")],
        current_time=create_pendulum_time(year=2020, month=1, day=5, hour=4),
    ),
    "self_dependency_start_date_changed": AssetReconciliationScenario(
        assets=one_asset_self_dependency_later_start_date,
        unevaluated_runs=[],
        cursor_from=AssetReconciliationScenario(
            assets=one_asset_self_dependency,
            unevaluated_runs=[],
            expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="2020-01-01")],
            current_time=create_pendulum_time(year=2020, month=1, day=2, hour=4),
        ),
        expected_run_requests=[run_request(asset_keys=["asset1"], partition_key="2023-01-01")],
        # this date changing business is not handled by the current implementation of the test
        supports_with_external_asset_graph=False,
    ),
    "self_dependency_multipartitioned": AssetReconciliationScenario(
        assets=multipartitioned_self_dependency,
        unevaluated_runs=[],
        expected_run_requests=[
            run_request(
                asset_keys=["asset1"],
                partition_key=MultiPartitionKey({"time": key_tuple[0], "abc": key_tuple[1]}),
            )
            for key_tuple in [("2020-01-01", "a"), ("2020-01-01", "b"), ("2020-01-01", "c")]
        ],
        current_time=create_pendulum_time(year=2020, month=1, day=2, hour=4),
    ),
    "self_dependency_prior_multipartition_materialized": AssetReconciliationScenario(
        assets=multipartitioned_self_dependency,
        unevaluated_runs=[
            single_asset_run(
                asset_key="asset1",
                partition_key=MultiPartitionKey({"time": "2020-01-01", "abc": "a"}),
            )
        ],
        cursor_from=AssetReconciliationScenario(
            assets=multipartitioned_self_dependency,
            unevaluated_runs=[],
        ),
        expected_run_requests=[
            run_request(
                asset_keys=["asset1"],
                partition_key=MultiPartitionKey({"time": "2020-01-02", "abc": "a"}),
            )
        ],
        current_time=create_pendulum_time(year=2020, month=1, day=3, hour=4),
    ),
    "unpartitioned_downstream_of_asymmetric_time_assets_in_series": AssetReconciliationScenario(
        assets=unpartitioned_downstream_of_asymmetric_time_assets_in_series,
        unevaluated_runs=[
            run(["asset1"], partition_key)
            for partition_key in [f"2023-01-0{x}" for x in range(5, 9)]
        ]
        + [
            run(["asset2"], partition_key)
            for partition_key in [f"2023-01-0{x}" for x in range(1, 9)]
        ],
        current_time=create_pendulum_time(2023, 1, 9, 0),
        expected_run_requests=[run_request(asset_keys=["unpartitioned"])],
    ),
    "upstream_starts_later_than_downstream": AssetReconciliationScenario(
        assets=upstream_starts_later_than_downstream,
        unevaluated_runs=[
            single_asset_run("asset1", "2023-01-01-03:00"),
            single_asset_run("asset1", "2023-01-01-04:00"),
        ],
        cursor_from=AssetReconciliationScenario(
            assets=upstream_starts_later_than_downstream,
            unevaluated_runs=[],
        ),
        current_time=create_pendulum_time(2023, 1, 1, 5),
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="2023-01-01-03:00"),
            run_request(asset_keys=["asset2"], partition_key="2023-01-01-04:00"),
        ],
    ),
    "one_parent_starts_later_and_nonexistent_upstream_partitions_allowed": (
        AssetReconciliationScenario(
            assets=one_parent_starts_later_and_nonexistent_upstream_partitions_allowed,
            unevaluated_runs=[
                single_asset_run("asset1", "2023-01-01-03:00"),
                single_asset_run("asset1", "2023-01-01-04:00"),
            ]
            + [single_asset_run("asset2", f"2023-01-01-0{x}:00") for x in range(0, 5)],
            current_time=create_pendulum_time(2023, 1, 1, 5),
            expected_run_requests=[
                run_request(asset_keys=["asset3"], partition_key=f"2023-01-01-0{x}:00")
                for x in range(0, 5)
            ],
        )
    ),
    "one_parent_starts_later_and_nonexistent_upstream_partitions_not_allowed": (
        AssetReconciliationScenario(
            assets=one_parent_starts_later_and_nonexistent_upstream_partitions_not_allowed,
            unevaluated_runs=[
                single_asset_run("asset1", "2023-01-01-03:00"),
                single_asset_run("asset1", "2023-01-01-04:00"),
            ]
            + [single_asset_run("asset2", f"2023-01-01-0{x}:00") for x in range(0, 5)],
            current_time=create_pendulum_time(2023, 1, 1, 5),
            expected_run_requests=[
                run_request(asset_keys=["asset3"], partition_key="2023-01-01-03:00"),
                run_request(asset_keys=["asset3"], partition_key="2023-01-01-04:00"),
            ],
        )
    ),
    "hourly_with_daily_downstream_nonexistent_upstream_partitions_allowed": AssetReconciliationScenario(
        assets=hourly_with_daily_downstream_nonexistent_upstream_partitions_allowed,
        unevaluated_runs=[
            single_asset_run("asset1", f"2023-01-01-{str(x).zfill(2)}:00")
            for x in range(0, 9)
            # partitions 2023-01-01-00:00 to 2023-01-01-08:00 materialized
        ],
        current_time=create_pendulum_time(2023, 1, 1, 9),
        expected_run_requests=[
            run_request(asset_keys=["asset2"], partition_key="2023-01-01"),
        ],
    ),
    "hourly_with_daily_downstream_nonexistent_upstream_partitions_not_allowed": AssetReconciliationScenario(
        assets=hourly_with_daily_downstream_nonexistent_upstream_partitions_not_allowed,
        unevaluated_runs=[
            single_asset_run("asset1", f"2023-01-01-{str(x).zfill(2)}:00")
            for x in range(0, 9)
            # partitions 2023-01-01-00:00 to 2023-01-01-08:00 materialized
        ],
        current_time=create_pendulum_time(2023, 1, 1, 9),
        expected_run_requests=[],
    ),
}
