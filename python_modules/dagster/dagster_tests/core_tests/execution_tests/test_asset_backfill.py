"""
To consider
- Multiple backfills target the same asset
- Parent assets not included in the backfill
- Failure
- Failure with transitive dependencies
- Two parents
- Two children
- Asset has two parents and one succeeds and one fails
- Asset has two parents and one is materialized and the other isn't
- Materialization happens to one of the asset partitions in the backfill, outside of the backfill
- Asset has two parents and only one is in the backfill
- Self-deps
- Non-partitioned assets
- Partition mappings
- Multi-assets
- Reconciliation sensor should avoid targeting targets of ongoing backfills
"""
from typing import AbstractSet, Dict, Mapping, NamedTuple, Optional, Sequence, Set, Union, cast
from unittest.mock import MagicMock, patch

import pytest
from dagster_tests.definitions_tests.test_asset_reconciliation_sensor import (
    RunSpec,
    do_run,
    one_asset_one_partition,
    one_asset_two_partitions,
    two_assets_in_sequence_fan_in_partitions,
    two_assets_in_sequence_fan_out_partitions,
    two_assets_in_sequence_one_partition,
    two_assets_in_sequence_two_partitions,
)

from dagster import (
    AssetKey,
    AssetSelection,
    AssetsDefinition,
    DagsterInstance,
    Definitions,
    PartitionsDefinition,
    RunRequest,
    SourceAsset,
)
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.execution.asset_backfill import (
    AssetBackfillData,
    execute_asset_backfill_iteration_inner,
)
from dagster._core.host_representation.external_data import external_asset_graph_from_defs


class AssetBackfillScenario(NamedTuple):
    assets: Sequence[Union[SourceAsset, AssetsDefinition]]
    unevaluated_runs: Sequence[RunSpec] = []
    expected_run_requests: Optional[Sequence[RunRequest]] = None
    expected_iterations: Optional[int] = None


assets_by_repo_name_by_scenario_name: Mapping[str, Mapping[str, Sequence[AssetsDefinition]]] = {
    "one_asset_one_partition": {"repo": one_asset_one_partition},
    "one_asset_two_partitions": {"repo": one_asset_two_partitions},
    "two_assets_in_sequence_one_partition": {"repo": two_assets_in_sequence_one_partition},
    "two_assets_in_sequence_one_partition_cross_repo": {
        "repo1": [two_assets_in_sequence_one_partition[0]],
        "repo2": [two_assets_in_sequence_one_partition[1]],
    },
    "two_assets_in_sequence_two_partitions": {"repo": two_assets_in_sequence_two_partitions},
    "two_assets_in_sequence_fan_in_partitions": {"repo": two_assets_in_sequence_fan_in_partitions},
    "two_assets_in_sequence_fan_out_partitions": {
        "repo": two_assets_in_sequence_fan_out_partitions
    },
}


@pytest.mark.parametrize("some_or_all", ["all", "some"])
@pytest.mark.parametrize("failures", ["no_failures", "root_failures", "random_half_failures"])
@pytest.mark.parametrize("scenario_name", list(assets_by_repo_name_by_scenario_name.keys()))
def test_scenario_to_completion(scenario_name: str, failures: str, some_or_all: str):
    assets_by_repo_name = assets_by_repo_name_by_scenario_name[scenario_name]

    with patch(
        "dagster._core.host_representation.external_data.get_builtin_partition_mapping_types"
    ) as get_builtin_partition_mapping_types:
        get_builtin_partition_mapping_types.return_value = tuple(
            assets_def.infer_partition_mapping(dep_key).__class__
            for assets in assets_by_repo_name.values()
            for assets_def in assets
            for dep_key in assets_def.dependency_keys
        )
        asset_graph = external_asset_graph_from_assets_by_repo_name(assets_by_repo_name)

    asset_keys = asset_graph.all_asset_keys
    root_asset_keys = AssetSelection.keys(*asset_keys).sources().resolve(asset_graph)

    if some_or_all == "all":
        target_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        for assets in assets_by_repo_name.values():
            for asset_def in assets:
                partitions_def = cast(PartitionsDefinition, asset_def.partitions_def)
                target_subsets_by_asset_key[
                    asset_def.key
                ] = partitions_def.empty_subset().with_partition_keys(
                    partitions_def.get_partition_keys()
                )
    elif some_or_all == "some":
        # all partitions downstream of half of the partitions in each root asset
        root_asset_partitions: Set[AssetKeyPartitionKey] = set()
        for root_asset_key in root_asset_keys:
            partitions_def = asset_graph.get_partitions_def(root_asset_key)
            assert partitions_def is not None
            partition_keys = list(partitions_def.get_partition_keys())
            start_index = len(partition_keys) // 2
            chosen_partition_keys = partition_keys[start_index:]
            root_asset_partitions.update(
                AssetKeyPartitionKey(root_asset_key, partition_key)
                for partition_key in chosen_partition_keys
            )

        target_asset_partitions = asset_graph.bfs_filter_asset_partitions(
            lambda _a, _b: True, root_asset_partitions
        )

        target_subsets_by_asset_key: Dict[AssetKey, PartitionsSubset] = {}
        for asset_key, partition_key in target_asset_partitions:
            assert partition_key is not None
            partitions_def = asset_graph.get_partitions_def(asset_key)
            assert partitions_def is not None
            subset = target_subsets_by_asset_key.get(asset_key, partitions_def.empty_subset())
            target_subsets_by_asset_key[asset_key] = subset.with_partition_keys([partition_key])

    else:
        assert False

    if failures == "no_failures":
        fail_asset_partitions: Set[AssetKeyPartitionKey] = set()
    elif failures == "root_failures":
        fail_asset_partitions: Set[AssetKeyPartitionKey] = {
            AssetKeyPartitionKey(root_asset_key, partition_key)
            for root_asset_key in root_asset_keys
            for partition_key in target_subsets_by_asset_key[root_asset_key].get_partition_keys()
        }
    elif failures == "random_half_failures":
        fail_asset_partitions: Set[AssetKeyPartitionKey] = {
            AssetKeyPartitionKey(asset_key, partition_key)
            for asset_key, subset in target_subsets_by_asset_key.items()
            for partition_key in subset.get_partition_keys()
            if hash(str(asset_key) + partition_key) % 2 == 0
        }

    else:
        assert False

    backfill = AssetBackfillData.empty(target_subsets_by_asset_key, asset_graph)
    run_backfill_to_completion(
        asset_graph, assets_by_repo_name, "backfillid_x", backfill, fail_asset_partitions
    )


def run_backfill_to_completion(
    asset_graph: ExternalAssetGraph,
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
    backfill_id: str,
    backfill_data: AssetBackfillData,
    fail_asset_partitions: AbstractSet[AssetKeyPartitionKey],
) -> None:
    iteration_count = 0
    instance = DagsterInstance.ephemeral()

    # assert each asset partition only targeted once
    requested_asset_partitions: Set[AssetKeyPartitionKey] = set()

    while not backfill_data.is_complete():
        iteration_count += 1
        result1 = execute_asset_backfill_iteration_inner(
            backfill_id=backfill_id,
            asset_backfill_data=backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )
        # iteration_count += 1
        assert result1.backfill_data != backfill_data

        # if nothing changes, nothing should happen in the iteration
        result2 = execute_asset_backfill_iteration_inner(
            backfill_id=backfill_id,
            asset_backfill_data=result1.backfill_data,
            asset_graph=asset_graph,
            instance=instance,
        )
        assert result2.backfill_data == result1.backfill_data
        assert result2.run_requests == []

        backfill_data = result2.backfill_data

        for run_request in result1.run_requests:
            for asset_key in run_request.asset_selection:
                asset_partition = AssetKeyPartitionKey(asset_key, run_request.partition_key)
                assert (
                    asset_partition not in requested_asset_partitions
                ), f"{asset_partition} requested twice. Requested: {requested_asset_partitions}"
                requested_asset_partitions.add(asset_partition)
                # TODO: assert that partitions downstream of failures are not requested

            assets = assets_by_repo_name[
                asset_graph.get_repository_handle(run_request.asset_selection[0]).repository_name
            ]
            do_run(
                all_assets=assets,
                asset_keys=run_request.asset_selection,
                partition_key=run_request.partition_key,
                instance=instance,
                failed_asset_keys=[
                    asset_key
                    for asset_key in run_request.asset_selection
                    if AssetKeyPartitionKey(asset_key, run_request.partition_key)
                    in fail_asset_partitions
                ],
                tags=run_request.tags,
            )

    assert iteration_count <= len(requested_asset_partitions) + 1

    # TODO: expected iterations
    # if there are no non-identify partiion mappings, the number of iterations should be the number
    # of partitions
    # if scenario.expected_iterations:
    #     assert iteration_count == scenario.expected_iterations


def external_asset_graph_from_assets_by_repo_name(
    assets_by_repo_name: Mapping[str, Sequence[AssetsDefinition]],
) -> ExternalAssetGraph:
    from_repository_handles_and_external_asset_nodes = []

    for repo_name, assets in assets_by_repo_name.items():

        repo = Definitions(assets=assets).get_repository_def()

        external_asset_nodes = external_asset_graph_from_defs(
            repo.get_all_pipelines(), source_assets_by_key=repo.source_assets_by_key
        )
        repo_handle = MagicMock(repository_name=repo_name)
        from_repository_handles_and_external_asset_nodes.extend(
            [(repo_handle, asset_node) for asset_node in external_asset_nodes]
        )

    return ExternalAssetGraph.from_repository_handles_and_external_asset_nodes(
        from_repository_handles_and_external_asset_nodes
    )
