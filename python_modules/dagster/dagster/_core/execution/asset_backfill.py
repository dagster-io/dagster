import json
from typing import AbstractSet, Iterable, List, Mapping, NamedTuple, Optional, Sequence, Set, cast

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
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class AssetBackfillData(NamedTuple):
    """Has custom serialization instead of standard Dagster NamedTuple serialization because the
    asset graph is required to build the AssetGraphSubset objects.
    """

    target_asset_partitions: AssetGraphSubset
    roots_were_requested: bool
    latest_storage_id: Optional[int]
    materialized_asset_partitions: AssetGraphSubset
    # also includes asset partitions within the backfill that are downstream of failed asset
    # partitions
    failed_asset_partitions: AssetGraphSubset

    def is_complete(self) -> bool:
        return all(
            len(self.materialized_asset_partitions.get_partitions_subset(asset_key))
            + len(self.failed_asset_partitions.get_partitions_subset(asset_key))
            == len(self.target_asset_partitions.get_partitions_subset(asset_key))
            for asset_key in self.target_asset_partitions.asset_keys
        )

    def get_target_root_asset_partitions(self) -> Iterable[AssetKeyPartitionKey]:
        root_asset_keys = (
            AssetSelection.keys(*self.target_asset_partitions.asset_keys)
            .sources()
            .resolve(self.target_asset_partitions.asset_graph)
        )
        return [
            AssetKeyPartitionKey(asset_key, partition_key)
            for asset_key in root_asset_keys
            for partition_key in self.target_asset_partitions.get_partitions_subset(
                asset_key
            ).get_partition_keys()
        ]

    @classmethod
    def empty(
        cls,
        target_subsets_by_asset_key: Mapping[AssetKey, PartitionsSubset],
        asset_graph: AssetGraph,
    ) -> "AssetBackfillData":
        return cls(
            target_asset_partitions=AssetGraphSubset(target_subsets_by_asset_key, asset_graph),
            roots_were_requested=False,
            materialized_asset_partitions=AssetGraphSubset({}, asset_graph),
            failed_asset_partitions=AssetGraphSubset({}, asset_graph),
            latest_storage_id=None,
        )

    @classmethod
    def from_serialized(cls, serialized: str, asset_graph: AssetGraph) -> "AssetBackfillData":
        storage_dict = json.loads(serialized)

        return cls(
            target_asset_partitions=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_target_asset_partitions"], asset_graph
            ),
            roots_were_requested=storage_dict["roots_were_requested"],
            materialized_asset_partitions=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_materialized_asset_partitions"], asset_graph
            ),
            failed_asset_partitions=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_failed_asset_partitions"], asset_graph
            ),
            latest_storage_id=storage_dict["latest_storage_id"],
        )

    def serialize(self) -> str:
        storage_dict = {
            "roots_were_requested": self.roots_were_requested,
            "serialized_target_asset_partitions": self.target_asset_partitions.to_storage_dict(),
            "latest_storage_id": self.latest_storage_id,
            "serialized_materialized_asset_partitions": self.materialized_asset_partitions.to_storage_dict(),
            "serialized_failed_asset_partitions": self.failed_asset_partitions.to_storage_dict(),
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
    instance: "DagsterInstance",
) -> AssetBackfillIterationResult:
    """Core logic of a backfill iteration. Has no side effects."""
    instance_queryer = CachingInstanceQueryer(instance=instance)

    initial_candidates: Set[AssetKeyPartitionKey] = set()
    request_roots = not asset_backfill_data.roots_were_requested
    if request_roots:
        initial_candidates.update(asset_backfill_data.get_target_root_asset_partitions())

    (
        parent_materialized_asset_partitions,
        next_latest_storage_id,
    ) = find_parent_materialized_asset_partitions(
        asset_graph=asset_graph,
        instance_queryer=instance_queryer,
        target_asset_selection=AssetSelection.keys(
            *asset_backfill_data.target_asset_partitions.asset_keys
        ),
        latest_storage_id=asset_backfill_data.latest_storage_id,
    )
    initial_candidates.update(parent_materialized_asset_partitions)

    recently_materialized_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]] = {
        asset_key: {
            cast(str, record.partition_key)
            for record in instance_queryer.get_materialization_records(
                asset_key=asset_key, after_cursor=asset_backfill_data.latest_storage_id
            )
        }
        for asset_key in asset_backfill_data.target_asset_partitions.asset_keys
    }

    updated_materialized_asset_partitions = (
        asset_backfill_data.materialized_asset_partitions
        | recently_materialized_partitions_by_asset_key
    )

    failed_asset_partitions = AssetGraphSubset.from_asset_partition_set(
        asset_graph.bfs_filter_asset_partitions(
            lambda asset_partitions, _: any(
                asset_partition in asset_backfill_data.target_asset_partitions
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
            materialized_asset_partitions=updated_materialized_asset_partitions,
            target_asset_partitions=asset_backfill_data.target_asset_partitions,
            failed_asset_partitions=failed_asset_partitions,
        ),
        initial_asset_partitions=initial_candidates,
    )

    run_requests = build_run_requests(
        asset_partitions_to_request, asset_graph, {BACKFILL_ID_TAG: backfill_id}
    )

    updated_asset_backfill_data = AssetBackfillData(
        target_asset_partitions=asset_backfill_data.target_asset_partitions,
        latest_storage_id=next_latest_storage_id or asset_backfill_data.latest_storage_id,
        roots_were_requested=asset_backfill_data.roots_were_requested or request_roots,
        materialized_asset_partitions=updated_materialized_asset_partitions,
        failed_asset_partitions=failed_asset_partitions,
    )
    return AssetBackfillIterationResult(run_requests, updated_asset_backfill_data)


def should_backfill_atomic_asset_partitions_unit(
    asset_graph: ExternalAssetGraph,
    candidates_unit: Iterable[AssetKeyPartitionKey],
    asset_partitions_to_request: AbstractSet[AssetKeyPartitionKey],
    target_asset_partitions: AssetGraphSubset,
    materialized_asset_partitions: AssetGraphSubset,
    failed_asset_partitions: AssetGraphSubset,
) -> bool:
    """
    Args:
        candidates_unit: A set of asset partitions that must all be materialized if any is
            materialized.
    """
    for candidate in candidates_unit:
        if (
            candidate not in target_asset_partitions
            or candidate in failed_asset_partitions
            or candidate in materialized_asset_partitions
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
                parent in target_asset_partitions
                and not can_run_with_parent
                and parent not in materialized_asset_partitions
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
        partition_key = run.tags[PARTITION_NAME_TAG]
        planned_asset_keys = instance_queryer.get_planned_materializations_for_run_from_events(
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
