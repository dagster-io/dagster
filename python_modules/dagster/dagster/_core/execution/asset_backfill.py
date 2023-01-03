import json
from typing import AbstractSet, Iterable, List, NamedTuple, Optional, Sequence, Set

from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_reconciliation_sensor import (
    build_run_requests,
    find_parent_materialized_asset_partitions,
)
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets_job import is_base_asset_job_name
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class AssetBackfillData(NamedTuple):
    """Has custom serialization instead of standard Dagster NamedTuple serialization because the
    asset graph is required to build the AssetGraphSubset objects.
    """

    target_subset: AssetGraphSubset
    requested_runs_for_target_roots: bool
    latest_storage_id: Optional[int]
    materialized_subset: AssetGraphSubset
    requested_subset: AssetGraphSubset
    failed_and_downstream_subset: AssetGraphSubset

    def is_complete(self) -> bool:
        return (
            (
                self.requested_subset | self.failed_and_downstream_subset
            ).num_partitions_and_non_partitioned_assets
            == self.target_subset.num_partitions_and_non_partitioned_assets
        )

    def get_target_root_asset_partitions(self) -> Iterable[AssetKeyPartitionKey]:
        root_asset_keys = (
            AssetSelection.keys(*self.target_subset.asset_keys)
            .sources()
            .resolve(self.target_subset.asset_graph)
        )
        return list(
            self.target_subset.filter_asset_keys(root_asset_keys).iterate_asset_partitions()
        )

    @classmethod
    def empty(cls, target_subset: AssetGraphSubset) -> "AssetBackfillData":
        asset_graph = target_subset.asset_graph
        return cls(
            target_subset=target_subset,
            requested_runs_for_target_roots=False,
            requested_subset=AssetGraphSubset(asset_graph),
            materialized_subset=AssetGraphSubset(asset_graph),
            failed_and_downstream_subset=AssetGraphSubset(asset_graph),
            latest_storage_id=None,
        )

    @classmethod
    def from_serialized(cls, serialized: str, asset_graph: AssetGraph) -> "AssetBackfillData":
        storage_dict = json.loads(serialized)

        return cls(
            target_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_target_subset"], asset_graph
            ),
            requested_runs_for_target_roots=storage_dict["requested_runs_for_target_roots"],
            requested_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_requested_subset"], asset_graph
            ),
            materialized_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_materialized_subset"], asset_graph
            ),
            failed_and_downstream_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_failed_subset"], asset_graph
            ),
            latest_storage_id=storage_dict["latest_storage_id"],
        )

    def serialize(self) -> str:
        storage_dict = {
            "requested_runs_for_target_roots": self.requested_runs_for_target_roots,
            "serialized_target_subset": self.target_subset.to_storage_dict(),
            "latest_storage_id": self.latest_storage_id,
            "serialized_requested_subset": self.requested_subset.to_storage_dict(),
            "serialized_materialized_subset": self.materialized_subset.to_storage_dict(),
            "serialized_failed_subset": self.failed_and_downstream_subset.to_storage_dict(),
        }
        return json.dumps(storage_dict)


def _get_implicit_job_name_for_assets(
    asset_graph: ExternalAssetGraph, asset_keys: Sequence[AssetKey]
) -> Optional[str]:
    job_names = set(asset_graph.get_job_names(asset_keys[0]))
    for asset_key in asset_keys[1:]:
        job_names &= set(asset_graph.get_job_names(asset_key))

    return next(job_name for job_name in job_names if is_base_asset_job_name(job_name))


class AssetBackfillIterationResult(NamedTuple):
    run_requests: Sequence[RunRequest]
    backfill_data: AssetBackfillData


def execute_asset_backfill_iteration_inner(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: ExternalAssetGraph,
    instance: DagsterInstance,
) -> AssetBackfillIterationResult:
    """
    Core logic of a backfill iteration. Has no side effects.

    Computes which runs should be requested, if any, as well as updated bookkeeping about the status
    of asset partitions targeted by the backfill.
    """
    instance_queryer = CachingInstanceQueryer(instance=instance)

    initial_candidates: Set[AssetKeyPartitionKey] = set()
    request_roots = not asset_backfill_data.requested_runs_for_target_roots
    if request_roots:
        initial_candidates.update(asset_backfill_data.get_target_root_asset_partitions())

    (
        parent_materialized_asset_partitions,
        next_latest_storage_id,
    ) = find_parent_materialized_asset_partitions(
        asset_graph=asset_graph,
        instance_queryer=instance_queryer,
        target_asset_selection=AssetSelection.keys(*asset_backfill_data.target_subset.asset_keys),
        latest_storage_id=asset_backfill_data.latest_storage_id,
    )
    initial_candidates.update(parent_materialized_asset_partitions)

    recently_materialized_asset_partitions = AssetGraphSubset(asset_graph)
    for asset_key in asset_backfill_data.target_subset.asset_keys:
        records = instance_queryer.get_materialization_records(
            asset_key=asset_key, after_cursor=asset_backfill_data.latest_storage_id
        )
        recently_materialized_asset_partitions |= {
            AssetKeyPartitionKey(asset_key, record.partition_key) for record in records
        }

    updated_materialized_asset_partitions = (
        asset_backfill_data.materialized_subset | recently_materialized_asset_partitions
    )

    failed_and_downstream_subset = AssetGraphSubset.from_asset_partition_set(
        asset_graph.bfs_filter_asset_partitions(
            lambda asset_partitions, _: any(
                asset_partition in asset_backfill_data.target_subset
                for asset_partition in asset_partitions
            ),
            _get_failed_asset_partitions(instance_queryer, backfill_id),
        ),
        asset_graph,
    )

    asset_partitions_to_request = asset_graph.bfs_filter_asset_partitions(
        lambda unit, visited: should_backfill_atomic_asset_partitions_unit(
            candidates_unit=unit,
            asset_partitions_to_request=visited,
            asset_graph=asset_graph,
            materialized_subset=updated_materialized_asset_partitions,
            target_subset=asset_backfill_data.target_subset,
            failed_and_downstream_subset=failed_and_downstream_subset,
        ),
        initial_asset_partitions=initial_candidates,
    )

    run_requests = build_run_requests(
        asset_partitions_to_request, asset_graph, {BACKFILL_ID_TAG: backfill_id}
    )

    updated_asset_backfill_data = AssetBackfillData(
        target_subset=asset_backfill_data.target_subset,
        latest_storage_id=next_latest_storage_id or asset_backfill_data.latest_storage_id,
        requested_runs_for_target_roots=asset_backfill_data.requested_runs_for_target_roots
        or request_roots,
        materialized_subset=updated_materialized_asset_partitions,
        failed_and_downstream_subset=failed_and_downstream_subset,
        requested_subset=asset_backfill_data.requested_subset | asset_partitions_to_request,
    )
    return AssetBackfillIterationResult(run_requests, updated_asset_backfill_data)


def should_backfill_atomic_asset_partitions_unit(
    asset_graph: ExternalAssetGraph,
    candidates_unit: Iterable[AssetKeyPartitionKey],
    asset_partitions_to_request: AbstractSet[AssetKeyPartitionKey],
    target_subset: AssetGraphSubset,
    materialized_subset: AssetGraphSubset,
    failed_and_downstream_subset: AssetGraphSubset,
) -> bool:
    """
    Args:
        candidates_unit: A set of asset partitions that must all be materialized if any is
            materialized.
    """
    for candidate in candidates_unit:
        if (
            candidate not in target_subset
            or candidate in failed_and_downstream_subset
            or candidate in materialized_subset
        ):
            return False

        for parent in asset_graph.get_parents_partitions(*candidate):
            can_run_with_parent = (
                parent in asset_partitions_to_request
                and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                and parent.partition_key == candidate.partition_key
                and asset_graph.get_repository_handle(candidate.asset_key)
                is asset_graph.get_repository_handle(parent.asset_key)
            )

            if (
                parent in target_subset
                and not can_run_with_parent
                and parent not in materialized_subset
            ):
                return False

    return True


def _get_failed_asset_partitions(
    instance_queryer: CachingInstanceQueryer, backfill_id: str
) -> Sequence[AssetKeyPartitionKey]:
    """
    Returns asset partitions that materializations were requested for as part of the backfill, but
    will not be materialized.

    Includes canceled asset partitions. Implementation assumes that successful runs won't have any
    failed partitions.
    """
    runs = instance_queryer.instance.get_runs(
        filters=RunsFilter(
            tags={BACKFILL_ID_TAG: backfill_id},
            statuses=[DagsterRunStatus.CANCELED, DagsterRunStatus.FAILURE],
        )
    )

    result: List[AssetKeyPartitionKey] = []

    for run in runs:
        partition_key = run.tags.get(PARTITION_NAME_TAG)
        planned_asset_keys = instance_queryer.get_planned_materializations_for_run(
            run_id=run.run_id
        )
        completed_asset_keys = instance_queryer.get_current_materializations_for_run(
            run_id=run.run_id
        )
        result.extend(
            AssetKeyPartitionKey(asset_key, partition_key)
            for asset_key in planned_asset_keys - completed_asset_keys
        )

    return result
