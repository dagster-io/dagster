import datetime

from dagster import PartitionKeyRange
from dagster._core.definitions.auto_materialize_rule import AutoMaterializeRule
from dagster._core.definitions.auto_materialize_rule_evaluation import (
    AutoMaterializeRuleEvaluation,
    ParentUpdatedRuleEvaluationData,
)
from dagster._core.definitions.events import AssetKey
from dagster._time import create_datetime

from ...scenario_utils.base_scenario import (
    AssetEvaluationSpec,
    AssetReconciliationScenario,
    asset_def,
    observable_source_asset_def,
    run,
    run_request,
)
from .partition_scenarios import hourly_partitions_def, two_partitions_partitions_def

unpartitioned_downstream_of_observable_source = [
    observable_source_asset_def("source_asset"),
    asset_def("asset1", ["source_asset"]),
]

partitioned_downstream_of_observable_source = [
    observable_source_asset_def("source_asset"),
    asset_def(
        "asset1",
        ["source_asset"],
        partitions_def=hourly_partitions_def,
    ),
]

downstream_of_multiple_observable_source_assets = [
    observable_source_asset_def("source_asset1"),
    observable_source_asset_def("source_asset2"),
    asset_def("asset1", ["source_asset1"]),
    asset_def("asset2", ["source_asset2"]),
    asset_def("asset3", ["asset1", "asset2"]),
]

downstream_of_unchanging_observable_source = [
    observable_source_asset_def("source_asset1", minutes_to_change=10**100),
    asset_def("asset1", ["source_asset1"]),
]

downstream_of_slowly_changing_observable_source = [
    observable_source_asset_def("source_asset1", minutes_to_change=30),
    asset_def("asset1", ["source_asset1"]),
]

partitioned_downstream_of_changing_observable_source = [
    observable_source_asset_def("source_asset", partitions_def=two_partitions_partitions_def),
    asset_def("asset1", ["source_asset"], partitions_def=two_partitions_partitions_def),
]
partitioned_downstream_of_unchanging_observable_source = [
    observable_source_asset_def(
        "source_asset", partitions_def=two_partitions_partitions_def, minutes_to_change=10**100
    ),
    asset_def("asset1", ["source_asset"], partitions_def=two_partitions_partitions_def),
]

observable_source_asset_scenarios = {
    "observable_to_unpartitioned0": AssetReconciliationScenario(
        assets=unpartitioned_downstream_of_observable_source,
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
        ],
        expected_run_requests=[run_request(["asset1"])],
    ),
    "observable_to_unpartitioned1": AssetReconciliationScenario(
        assets=unpartitioned_downstream_of_observable_source,
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
            run(["asset1"]),
        ],
        expected_run_requests=[],
    ),
    "observable_to_unpartitioned2": AssetReconciliationScenario(
        assets=unpartitioned_downstream_of_observable_source,
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
            run(["asset1"]),
            run(["source_asset"], is_observation=True),
        ],
        expected_run_requests=[run_request(["asset1"])],
    ),
    "observable_to_unpartitioned_with_failure": AssetReconciliationScenario(
        assets=unpartitioned_downstream_of_observable_source,
        cursor_from=AssetReconciliationScenario(
            assets=unpartitioned_downstream_of_observable_source,
            unevaluated_runs=[
                run(["source_asset"], is_observation=True),
            ],
            expected_run_requests=[run_request(["asset1"])],
        ),
        unevaluated_runs=[
            run(["asset1"], failed_asset_keys=["asset1"]),
        ],
        # should not request again
        expected_run_requests=[],
    ),
    "observable_to_partitioned": AssetReconciliationScenario(
        assets=partitioned_downstream_of_observable_source,
        current_time=create_datetime(year=2013, month=1, day=6, hour=1),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
        ]
        + [
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-06-00:00")
            )
        ],
        expected_run_requests=[],
    ),
    "observable_to_partitioned2": AssetReconciliationScenario(
        assets=partitioned_downstream_of_observable_source,
        current_time=create_datetime(year=2013, month=1, day=6, hour=2),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
        ]
        + [
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-00:00", end="2013-01-06-00:00")
            )
        ]
        + [
            run(["source_asset"], is_observation=True),
        ]
        + [
            # update some subset of the partitions
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-05-04:00", end="2013-01-05-17:00")
            )
        ],
        expected_run_requests=[
            # only execute the missing one
            run_request(asset_keys=["asset1"], partition_key="2013-01-06-01:00")
        ],
    ),
    "multiple_observable": AssetReconciliationScenario(
        assets=downstream_of_multiple_observable_source_assets,
        unevaluated_runs=[
            run(["source_asset1", "source_asset2"], is_observation=True),
            run(["asset1", "asset2", "asset3"]),
            run(["source_asset1"], is_observation=True),
        ],
        expected_run_requests=[
            run_request(asset_keys=["asset1", "asset3"]),
        ],
    ),
    "unchanging_observable": AssetReconciliationScenario(
        assets=downstream_of_unchanging_observable_source,
        unevaluated_runs=[
            run(["source_asset1"], is_observation=True),
            run(["asset1"]),
            run(["source_asset1"], is_observation=True),
        ],
        expected_run_requests=[],
    ),
    "unchanging_observable_many_observations": AssetReconciliationScenario(
        assets=downstream_of_unchanging_observable_source,
        cursor_from=AssetReconciliationScenario(
            assets=downstream_of_unchanging_observable_source,
            unevaluated_runs=[
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
            ],
            expected_run_requests=[run_request(["asset1"])],
        ),
        unevaluated_runs=[],
        expected_run_requests=[],
    ),
    "partitioned_downstream_of_changing_observable_source": AssetReconciliationScenario(
        assets=partitioned_downstream_of_changing_observable_source,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_downstream_of_changing_observable_source,
            unevaluated_runs=[
                run(["source_asset"], is_observation=True),
                run(["asset1"], partition_key="a"),
            ],
            expected_run_requests=[
                run_request(["asset1"], partition_key="b"),
            ],
        ),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
            run(["source_asset"], is_observation=True),
            run(["asset1"], partition_key="a"),
            run(["asset1"], partition_key="b"),
            run(["source_asset"], is_observation=True),
        ],
        expected_run_requests=[
            run_request(["asset1"], partition_key="a"),
            run_request(["asset1"], partition_key="b"),
        ],
    ),
    "partitioned_downstream_of_changing_observable_source_observed": AssetReconciliationScenario(
        assets=partitioned_downstream_of_changing_observable_source,
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
            run(["asset1"], partition_key="a"),
        ],
        expected_run_requests=[
            run_request(["asset1"], partition_key="b"),
        ],
        expected_evaluations=[
            AssetEvaluationSpec(
                asset_key="asset1",
                rule_evaluations=[
                    (
                        AutoMaterializeRuleEvaluation(
                            rule_snapshot=AutoMaterializeRule.materialize_on_parent_updated().to_snapshot(),
                            evaluation_data=ParentUpdatedRuleEvaluationData(
                                updated_asset_keys=frozenset([AssetKey("source_asset")]),
                                will_update_asset_keys=frozenset(),
                            ),
                        ),
                        {"b"},
                    ),
                    (
                        AutoMaterializeRuleEvaluation(
                            rule_snapshot=AutoMaterializeRule.materialize_on_missing().to_snapshot(),
                            evaluation_data=None,
                        ),
                        {"b"},
                    ),
                ],
                num_requested=1,
            )
        ],
    ),
    "partitioned_downstream_of_changing_observable_source_empty": AssetReconciliationScenario(
        assets=partitioned_downstream_of_changing_observable_source,
        unevaluated_runs=[],
        expected_run_requests=[],
        expected_evaluations=[],
    ),
    "partitioned_downstream_of_unchanging_observable_source": AssetReconciliationScenario(
        assets=partitioned_downstream_of_unchanging_observable_source,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_downstream_of_unchanging_observable_source,
            unevaluated_runs=[
                run(["source_asset"], is_observation=True),
                run(["asset1"], partition_key="a"),
            ],
            expected_run_requests=[
                run_request(["asset1"], partition_key="b"),
            ],
        ),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
            run(["source_asset"], is_observation=True),
            run(["source_asset"], is_observation=True),
            run(["source_asset"], is_observation=True),
        ],
        expected_run_requests=[],
    ),
    "slowly_changing_observable_many_observations": AssetReconciliationScenario(
        assets=downstream_of_slowly_changing_observable_source,
        cursor_from=AssetReconciliationScenario(
            assets=downstream_of_slowly_changing_observable_source,
            unevaluated_runs=[
                # many observations of the same version
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                run(["source_asset1"], is_observation=True),
                # an observation of a new version
                run(["source_asset1"], is_observation=True),
            ],
            expected_run_requests=[run_request(["asset1"])],
            current_time=create_datetime(year=2020, month=1, day=1, hour=1),
            between_runs_delta=datetime.timedelta(minutes=7),
        ),
        current_time=create_datetime(year=2020, month=1, day=1, hour=1, minute=45),
        unevaluated_runs=[
            # another observation of the second version
            run(["source_asset1"], is_observation=True),
        ],
        expected_run_requests=[],
    ),
}
