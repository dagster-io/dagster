from dagster._core.definitions.partition import StaticPartitionsDefinition

from ...scenario_utils.base_scenario import AssetReconciliationScenario, asset_def, run, run_request

three_partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

# A code version is not set on the root asset so that rematerializing it will be guaranteed to
# produce a new data version.
all_unpartitioned = [
    asset_def("one"),
    asset_def("two", ["one"], code_version="0"),
    asset_def("three", ["two"], code_version="0"),
]

partitioned_to_unpartitioned = [
    asset_def("one", partitions_def=three_partitions_def),
    asset_def("two", ["one"], partitions_def=three_partitions_def, code_version="0"),
    asset_def("three", ["two"], code_version="0"),
]

unpartitioned_to_partitioned = [
    asset_def("one"),
    asset_def("two", ["one"], code_version="0"),
    asset_def("three", ["two"], partitions_def=three_partitions_def, code_version="0"),
]

partitioned_to_partitioned = [
    asset_def("one", partitions_def=three_partitions_def),
    asset_def("two", ["one"], partitions_def=three_partitions_def, code_version="0"),
    asset_def("three", ["two"], partitions_def=three_partitions_def, code_version="0"),
]

version_scenarios = {
    "all_unpartitioned_version_updated": AssetReconciliationScenario(
        assets=all_unpartitioned,
        cursor_from=AssetReconciliationScenario(
            assets=all_unpartitioned, unevaluated_runs=[run(["one", "two", "three"])]
        ),
        unevaluated_runs=[run(["one", "two"])],
        expected_run_requests=[run_request(["three"])],
    ),
    "all_unpartitioned_version_not_updated": AssetReconciliationScenario(
        assets=all_unpartitioned,
        cursor_from=AssetReconciliationScenario(
            assets=all_unpartitioned, unevaluated_runs=[run(["one", "two", "three"])]
        ),
        unevaluated_runs=[run(["two"])],
        expected_run_requests=[],
        requires_respect_materialization_data_versions=True,
    ),
    "partitioned_to_unpartitioned_version_updated": AssetReconciliationScenario(
        assets=partitioned_to_unpartitioned,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_to_unpartitioned,
            unevaluated_runs=[
                run(["one", "two"], partition_key="a"),
                run(["one", "two"], partition_key="b"),
                run(["one", "two"], partition_key="c"),
                run(["three"]),
            ],
        ),
        unevaluated_runs=[run(["one", "two"], partition_key="b")],
        expected_run_requests=[run_request(["three"])],
    ),
    "partitioned_to_unpartitioned_version_not_updated": AssetReconciliationScenario(
        assets=partitioned_to_unpartitioned,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_to_unpartitioned,
            unevaluated_runs=[
                run(["one", "two"], partition_key="a"),
                run(["one", "two"], partition_key="b"),
                run(["one", "two"], partition_key="c"),
                run(["three"]),
            ],
        ),
        unevaluated_runs=[run(["two"], partition_key="c")],
        expected_run_requests=[],
        requires_respect_materialization_data_versions=True,
    ),
    "unpartitioned_to_partitioned_version_updated": AssetReconciliationScenario(
        assets=unpartitioned_to_partitioned,
        cursor_from=AssetReconciliationScenario(
            assets=unpartitioned_to_partitioned,
            unevaluated_runs=[
                run(["one", "two"]),
                run(["three"], partition_key="a"),
                run(["three"], partition_key="b"),
                run(["three"], partition_key="c"),
            ],
        ),
        unevaluated_runs=[run(["one", "two"])],
        expected_run_requests=[
            run_request(["three"], partition_key="a"),
            run_request(["three"], partition_key="b"),
            run_request(["three"], partition_key="c"),
        ],
    ),
    "unpartitioned_to_partitioned_version_not_updated": AssetReconciliationScenario(
        assets=unpartitioned_to_partitioned,
        cursor_from=AssetReconciliationScenario(
            assets=unpartitioned_to_partitioned,
            unevaluated_runs=[
                run(["one", "two"]),
                run(["three"], partition_key="a"),
                run(["three"], partition_key="b"),
                run(["three"], partition_key="c"),
            ],
        ),
        unevaluated_runs=[run(["two"])],
        expected_run_requests=[],
        requires_respect_materialization_data_versions=True,
    ),
    "partitioned_to_partitioned_version_updated": AssetReconciliationScenario(
        assets=partitioned_to_partitioned,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_to_partitioned,
            unevaluated_runs=[
                run(["one", "two", "three"], partition_key="a"),
                run(["one", "two", "three"], partition_key="b"),
                run(["one", "two", "three"], partition_key="c"),
            ],
        ),
        unevaluated_runs=[
            run(["one", "two"], partition_key="b"),
            run(["one", "two"], partition_key="c"),
        ],
        expected_run_requests=[
            run_request(["three"], partition_key="b"),
            run_request(["three"], partition_key="c"),
        ],
    ),
    "partitioned_to_partitioned_version_not_updated": AssetReconciliationScenario(
        assets=partitioned_to_partitioned,
        cursor_from=AssetReconciliationScenario(
            assets=partitioned_to_partitioned,
            unevaluated_runs=[
                run(["one", "two", "three"], partition_key="a"),
                run(["one", "two", "three"], partition_key="b"),
                run(["one", "two", "three"], partition_key="c"),
            ],
        ),
        unevaluated_runs=[
            run(["two"], partition_key="b"),
            run(["two"], partition_key="c"),
        ],
        expected_run_requests=[],
        requires_respect_materialization_data_versions=True,
    ),
}
