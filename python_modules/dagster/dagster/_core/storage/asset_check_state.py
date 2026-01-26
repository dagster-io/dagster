from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Optional, TypeAlias

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
    AssetCheckPartitionInfo,
)
from dagster._core.storage.dagster_run import FINISHED_STATUSES, DagsterRunStatus, RunsFilter

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

StatusSubsets: TypeAlias = Mapping[
    AssetCheckExecutionResolvedStatus, SerializableEntitySubset[AssetCheckKey]
]
InProgressRuns: TypeAlias = Mapping[str, SerializableEntitySubset[AssetCheckKey]]


@whitelist_for_serdes
@record
class AssetCheckState(LoadableBy[tuple[AssetCheckKey, Optional[PartitionsDefinition]]]):
    latest_storage_id: int
    subsets: StatusSubsets
    in_progress_runs: InProgressRuns

    def compatible_with(self, partitions_def: Optional[PartitionsDefinition]) -> bool:
        subset = next(iter(self.subsets.values()), None)
        if subset is None:
            return True
        return subset.is_compatible_with_partitions_def(partitions_def)

    @classmethod
    def empty(cls) -> "AssetCheckState":
        return cls(latest_storage_id=0, subsets={}, in_progress_runs={})

    @classmethod
    def _blocking_batch_load(
        cls,
        keys: Iterable[tuple[AssetCheckKey, Optional[PartitionsDefinition]]],
        context: LoadingContext,
    ) -> Iterable[Optional["AssetCheckState"]]:
        keys = list(keys)
        mapping = context.instance.event_log_storage.get_asset_check_state(keys)
        return [mapping.get(check_key) for check_key, _ in keys]

    def with_updates(
        self,
        key: AssetCheckKey,
        partitions_def: Optional[PartitionsDefinition],
        partition_records: Sequence[AssetCheckPartitionInfo],
        run_statuses: Mapping[str, DagsterRunStatus],
    ) -> "AssetCheckState":
        latest_storage_id = max(
            (
                max(r.latest_check_event_storage_id, r.latest_materialization_storage_id or 0)
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
        return AssetCheckState(
            latest_storage_id=latest_storage_id,
            subsets=subsets,
            in_progress_runs=in_progress_runs,
        )


def bulk_update_asset_check_state(
    instance: "DagsterInstance",
    keys: Sequence[tuple[AssetCheckKey, Optional[PartitionsDefinition]]],
    initial_states: Mapping[AssetCheckKey, "AssetCheckState"],
) -> Mapping[AssetCheckKey, "AssetCheckState"]:
    check_keys = [key for key, _ in keys]
    partitions_defs_by_key = {key: partitions_def for key, partitions_def in keys}

    # we prefer to do a single fetch for all keys, so we use the minimum storage id of the initial states
    storage_id = min((state.latest_storage_id for state in initial_states.values()), default=0)
    infos = instance.event_log_storage.get_asset_check_partition_info(
        check_keys, after_storage_id=storage_id
    )

    # find the set of run ids we need to fetch to resolve the in-progress runs, and
    # group the partition infos by check key
    run_ids_to_fetch: set[str] = set().union(
        *(state.in_progress_runs.keys() for state in initial_states.values())
    )
    infos_by_key: dict[AssetCheckKey, list[AssetCheckPartitionInfo]] = defaultdict(list)
    for info in infos:
        infos_by_key[info.check_key].append(info)
        if info.latest_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
            run_ids_to_fetch.add(info.latest_planned_run_id)

    # do a bulk fetch for runs across all states
    finished_runs = (
        instance.get_runs(
            filters=RunsFilter(run_ids=list(run_ids_to_fetch), statuses=FINISHED_STATUSES)
        )
        if len(run_ids_to_fetch) > 0
        else []
    )
    finished_runs_status_by_id = {run.run_id: run.status for run in finished_runs}
    return {
        key: initial_states[key].with_updates(
            key, partitions_defs_by_key[key], infos_by_key[key], finished_runs_status_by_id
        )
        for key in check_keys
    }


def _valid_partition_key(
    partition_key: Optional[str], partitions_def: Optional[PartitionsDefinition]
) -> bool:
    if partitions_def is None:
        return partition_key is None
    else:
        return partition_key is not None and partitions_def.has_partition_key(partition_key)


def _process_partition_records(
    key: AssetCheckKey,
    partitions_def: Optional[PartitionsDefinition],
    subsets: StatusSubsets,
    in_progress_runs: InProgressRuns,
    partition_infos: Sequence[AssetCheckPartitionInfo],
) -> tuple[StatusSubsets, InProgressRuns]:
    """Returns a set of updated subsets based on new partition records and the latest materialization storage ids."""
    new_subsets = dict(subsets)
    new_in_progress_runs = dict(in_progress_runs)

    for partition_record in partition_infos:
        pk = partition_record.partition_key
        if not _valid_partition_key(pk, partitions_def):
            continue

        partition_subset = SerializableEntitySubset.from_coercible_value(key, pk, partitions_def)

        if partition_record.latest_execution_status == AssetCheckExecutionRecordStatus.PLANNED:
            # Add to IN_PROGRESS and track run
            new_subsets[AssetCheckExecutionResolvedStatus.IN_PROGRESS] = new_subsets[
                AssetCheckExecutionResolvedStatus.IN_PROGRESS
            ].compute_union(partition_subset)
            run_id = partition_record.latest_planned_run_id
            new_in_progress_runs[run_id] = new_in_progress_runs.get(
                run_id, SerializableEntitySubset.empty(key, partitions_def)
            ).compute_union(partition_subset)

        elif partition_record.latest_execution_status in (
            AssetCheckExecutionRecordStatus.SUCCEEDED,
            AssetCheckExecutionRecordStatus.FAILED,
        ):
            if partition_record.is_current:
                # Check is current, set appropriate status
                status = (
                    AssetCheckExecutionResolvedStatus.SUCCEEDED
                    if partition_record.latest_execution_status
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
    partitions_def: Optional[PartitionsDefinition],
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
    partitions_def: Optional[PartitionsDefinition],
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
        if run_status in FINISHED_STATUSES and run_id in in_progress_runs:
            resolved_run_ids.add(run_id)
            run_subset = in_progress_runs[run_id]
            if run_status == DagsterRunStatus.FAILURE:
                delta_execution_failed = delta_execution_failed.compute_union(run_subset)
            else:
                delta_skipped = delta_skipped.compute_union(run_subset)

    return delta_skipped, delta_execution_failed, resolved_run_ids
