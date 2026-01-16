from collections.abc import Iterable, Mapping, Sequence
from typing import Optional, TypeAlias

from dagster_shared.record import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.asset_key import AssetCheckKey
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.loader import LoadableBy, LoadingContext
from dagster._core.storage.asset_check_execution_record import (
    AssetCheckExecutionRecordStatus,
    AssetCheckExecutionResolvedStatus,
    AssetCheckPartitionRecord,
)
from dagster._core.storage.dagster_run import FINISHED_STATUSES, DagsterRunStatus, RunRecord

StatusSubsets: TypeAlias = Mapping[
    AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]
]
InProgressRuns: TypeAlias = Mapping[str, SerializableEntitySubset[AssetCheckKey]]


@whitelist_for_serdes
@record
class AssetCheckPartitionState(LoadableBy[tuple[AssetCheckKey, PartitionsDefinition]]):
    latest_storage_id: int
    subsets: StatusSubsets
    in_progress_runs: InProgressRuns

    def compatible_with(self, partitions_def: Optional[PartitionsDefinition]) -> bool:
        subset = next(iter(self.subsets.values()), None)
        if subset is None:
            return True
        return subset.is_compatible_with_partitions_def(partitions_def)

    @classmethod
    def empty(cls) -> "AssetCheckPartitionState":
        return cls(latest_storage_id=0, subsets={}, in_progress_runs={})

    @classmethod
    def _blocking_batch_load(
        cls, keys: Iterable[tuple[AssetCheckKey, PartitionsDefinition]], context: LoadingContext
    ) -> Iterable[Optional["AssetCheckPartitionState"]]:
        # for now, just return an empty state for each key
        return [cls.empty() for _ in keys]

    @classmethod
    async def gen_updated(
        cls,
        context: LoadingContext,
        key: tuple[AssetCheckKey, PartitionsDefinition],
    ) -> "AssetCheckPartitionState":
        """Returns a new state object that incorporates any changes that may have occurred since this
        state object was last stored. Used for use cases that require near real-time accuracy.
        """
        check_key, partitions_def = key
        state = await cls.gen(context, key) or cls.empty()
        check_records = context.instance.event_log_storage.get_asset_check_partition_records(
            check_key, after_storage_id=state.latest_storage_id
        )
        run_ids = [
            *state.in_progress_runs.keys(),
            *{
                r.last_planned_run_id
                for r in check_records
                if r.last_execution_status == AssetCheckExecutionRecordStatus.PLANNED
            },
        ]
        run_records = await RunRecord.gen_many(context, run_ids)
        run_statuses = {r.dagster_run.run_id: r.dagster_run.status for r in run_records if r}
        return state.with_updates(check_key, partitions_def, list(check_records), run_statuses)

    def with_updates(
        self,
        key: AssetCheckKey,
        partitions_def: PartitionsDefinition,
        partition_records: Sequence[AssetCheckPartitionRecord],
        run_statuses: Mapping[str, DagsterRunStatus],
    ) -> "AssetCheckPartitionState":
        latest_storage_id = max(
            (
                max(r.last_storage_id, r.last_materialization_storage_id or 0)
                for r in partition_records
            ),
            default=self.latest_storage_id,
        )

        subsets = {
            status: self.subsets.get(status, SerializableEntitySubset.empty(key, partitions_def))
            for status in AssetCheckExecutionResolvedStatus
        }
        in_progress_runs = dict(self.in_progress_runs)

        # update all subsets based on the new partition records
        subsets, in_progress_runs = _process_partition_records(
            key, partitions_def, subsets, in_progress_runs, partition_records
        )
        # then check the run statuses and resolve any previously in-progress runs that have completed
        subsets, in_progress_runs = _process_run_statuses(
            key, partitions_def, subsets, in_progress_runs, run_statuses
        )
        return AssetCheckPartitionState(
            latest_storage_id=latest_storage_id,
            subsets=subsets,
            in_progress_runs=in_progress_runs,
        )


def _process_partition_records(
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    subsets: StatusSubsets,
    in_progress_runs: InProgressRuns,
    partition_records: Sequence[AssetCheckPartitionRecord],
) -> tuple[StatusSubsets, InProgressRuns]:
    """Returns a set of updated subsets based on new partition records and the latest materialization storage ids."""
    new_subsets = dict(subsets)
    new_in_progress_runs = dict(in_progress_runs)

    for partition_record in partition_records:
        pk = partition_record.partition_key
        if pk is None or not partitions_def.has_partition_key(pk):
            continue

        partition_subset = SerializableEntitySubset.from_coercible_value(key, pk, partitions_def)

        if partition_record.last_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
            # Add to IN_PROGRESS and track run
            new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS] = new_subsets[
                AssetCheckExecutionResolvedStatus.IN_PROGRESS
            ].compute_union(partition_subset)
            run_id = partition_record.last_planned_run_id
            new_in_progress_runs[run_id] = new_in_progress_runs.get(
                run_id, SerializableEntitySubset.empty(key, partitions_def)
            ).compute_union(partition_subset)

        elif partition_record.last_execution_status in (
            AssetCheckExecutionRecordStatus.SUCCEEDED,
            AssetCheckExecutionRecordStatus.FAILED,
        ):
            if partition_record.is_current:
                # Check is current, set appropriate status
                status = (
                    AssetCheckExecutionResolvedStatus.SUCCEEDED
                    if partition_record.last_execution_status
                    == AssetCheckExecutionRecordStatus.SUCCEEDED
                    else AssetCheckExecutionResolvedStatus.FAILED
                )
                new_subsets[status] = new_subsets[status].compute_union(partition_subset)
            else:
                # new materialization, clear the check status
                for status in new_subsets:
                    new_subsets[status] = new_subsets[status].compute_difference(partition_subset)

    return new_subsets, new_in_progress_runs


def _process_run_statuses(
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    subsets: StatusSubsets,
    in_progress_runs: InProgressRuns,
    run_statuses: Mapping[str, DagsterRunStatus],
) -> tuple[StatusSubsets, InProgressRuns]:
    """Resolve in-progress runs that have completed.

    This checks if any runs tracked in in_progress_runs have finished,
    and moves their partitions to SKIPPED or EXECUTION_FAILED.
    """
    if not in_progress_runs:
        return subsets, in_progress_runs

    delta_skipped, delta_execution_failed, resolved_run_ids = _resolve_in_progress_subsets(
        key, partitions_def, in_progress_runs, run_statuses
    )

    new_in_progress_runs = {
        run_id: subset
        for run_id, subset in in_progress_runs.items()
        if run_id not in resolved_run_ids
    }

    new_subsets = dict(subsets)
    new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS] = (
        new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS]
        .compute_difference(delta_skipped)
        .compute_difference(delta_execution_failed)
    )
    new_subsets[AssetCheckExecutionResolvedStatus.SKIPPED] = new_subsets[
        AssetCheckExecutionResolvedStatus.SKIPPED
    ].compute_union(delta_skipped)
    new_subsets[AssetCheckExecutionResolvedStatus.EXECUTION_FAILED] = new_subsets[
        AssetCheckExecutionResolvedStatus.EXECUTION_FAILED
    ].compute_union(delta_execution_failed)

    return new_subsets, new_in_progress_runs


def _resolve_in_progress_subsets(
    key: AssetCheckKey,
    partitions_def: PartitionsDefinition,
    in_progress_runs: InProgressRuns,
    run_statuses: Mapping[str, DagsterRunStatus],
) -> tuple[
    SerializableEntitySubset[AssetCheckKey],
    SerializableEntitySubset[AssetCheckKey],
    set[str],
]:
    """Resolve in-progress runs that have completed.

    Returns:
        Tuple of (delta_skipped, delta_execution_failed, resolved_run_ids)
    """
    empty_subset = SerializableEntitySubset.empty(key, partitions_def)
    delta_skipped = empty_subset
    delta_execution_failed = empty_subset
    resolved_run_ids: set[str] = set()

    for run_id, run_status in run_statuses.items():
        if run_status in FINISHED_STATUSES:
            resolved_run_ids.add(run_id)
            run_subset = in_progress_runs[run_id]
            if run_status == DagsterRunStatus.FAILURE:
                delta_execution_failed = delta_execution_failed.compute_union(run_subset)
            else:
                delta_skipped = delta_skipped.compute_union(run_subset)

    return delta_skipped, delta_execution_failed, resolved_run_ids
