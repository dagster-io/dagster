from dagster import PartitionKeyRange
from dagster._seven.compat.pendulum import create_pendulum_time

from .asset_reconciliation_scenario import (
    AssetReconciliationScenario,
    asset_def,
    observable_source_asset_def,
    run,
    run_request,
)
from .partition_scenarios import hourly_partitions_def

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

observable_source_asset_scenarios = {
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
    "observable_to_partitioned": AssetReconciliationScenario(
        assets=partitioned_downstream_of_observable_source,
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
        ]
        + [
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-04:00", end="2013-01-07-03:00")
            )
        ],
        expected_run_requests=[],
    ),
    "observable_to_partitioned2": AssetReconciliationScenario(
        assets=partitioned_downstream_of_observable_source,
        current_time=create_pendulum_time(year=2013, month=1, day=7, hour=4),
        unevaluated_runs=[
            run(["source_asset"], is_observation=True),
        ]
        + [
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-04:00", end="2013-01-07-03:00")
            )
        ]
        + [
            run(["source_asset"], is_observation=True),
        ]
        + [
            # update some subset of the partitions
            run(["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-04:00", end="2013-01-06-17:00")
            )
        ],
        expected_run_requests=[
            # only execute the non-updated ones
            run_request(asset_keys=["asset1"], partition_key=partition_key)
            for partition_key in hourly_partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(start="2013-01-06-18:00", end="2013-01-07-03:00")
            )
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
}
