import json
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    cast,
)

from dagster import _check as check
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
from dagster._core.definitions.mode import DEFAULT_MODE_NAME
from dagster._core.definitions.run_request import RunRequest
from dagster._core.events import DagsterEventType
from dagster._core.host_representation.selector import PipelineSelector
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, PARTITION_NAME_TAG
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

if TYPE_CHECKING:
    from .backfill import PartitionBackfill


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

    def get_num_partitions(self) -> int:
        """
        Only valid when the same number of partitions are targeted in every asset.

        When not valid, raises an error.
        """
        asset_partition_nums = {
            len(subset) for subset in self.target_subset.partitions_subsets_by_asset_key.values()
        }
        if len(asset_partition_nums) == 0:
            return 0
        elif len(asset_partition_nums) == 1:
            return next(iter(asset_partition_nums))
        else:
            check.failed(
                "Can't compute number of partitions for asset backfill because different assets "
                "have different numbers of partitions"
            )

    def get_partition_names(self) -> Sequence[str]:
        """
        Only valid when the same number of partitions are targeted in every asset.

        When not valid, raises an error.
        """
        subsets = self.target_subset.partitions_subsets_by_asset_key.values()
        if len(subsets) == 0:
            return []

        first_subset = next(iter(subsets))
        if any(subset != subset for subset in subsets):
            check.failed(
                "Can't find partition names for asset backfill because different assets "
                "have different partitions"
            )

        return list(first_subset.get_partition_keys())

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


def execute_asset_backfill_iteration(
    backfill: "PartitionBackfill", workspace: BaseWorkspaceRequestContext, instance: DagsterInstance
) -> Iterable[None]:
    """
    Runs an iteration of the backfill, including submitting runs and updating the backfill object
    in the DB.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    from dagster._core.execution.backfill import BulkActionStatus

    asset_graph = ExternalAssetGraph.from_workspace(workspace)
    if backfill.serialized_asset_backfill_data is None:
        check.failed("Asset backfill missing serialized_asset_backfill_data")

    asset_backfill_data = AssetBackfillData.from_serialized(
        backfill.serialized_asset_backfill_data, asset_graph
    )

    result = None
    for result in execute_asset_backfill_iteration_inner(
        backfill_id=backfill.backfill_id,
        asset_backfill_data=asset_backfill_data,
        instance=instance,
        asset_graph=asset_graph,
    ):
        yield None

    if not isinstance(result, AssetBackfillIterationResult):
        check.failed(
            "Expected execute_asset_backfill_iteration_inner to return an"
            " AssetBackfillIterationResult"
        )

    updated_backfill = backfill.with_asset_backfill_data(result.backfill_data)
    if result.backfill_data.is_complete():
        updated_backfill = updated_backfill.with_status(BulkActionStatus.COMPLETED)

    for run_request in result.run_requests:
        yield None
        submit_run_request(
            run_request=run_request, asset_graph=asset_graph, workspace=workspace, instance=instance
        )

    instance.update_backfill(updated_backfill)


def submit_run_request(
    asset_graph: ExternalAssetGraph,
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: BaseWorkspaceRequestContext,
) -> None:
    """
    Creates and submits a run for the given run request
    """
    repo_handle = asset_graph.get_repository_handle(
        cast(Sequence[AssetKey], run_request.asset_selection)[0]
    )
    location_name = repo_handle.repository_location_origin.location_name
    repo_location = workspace.get_repository_location(
        repo_handle.repository_location_origin.location_name
    )
    job_name = _get_implicit_job_name_for_assets(
        asset_graph, cast(Sequence[AssetKey], run_request.asset_selection)
    )
    if job_name is None:
        check.failed(
            "Could not find an implicit asset job for the given assets:"
            f" {run_request.asset_selection}"
        )
    pipeline_selector = PipelineSelector(
        location_name=location_name,
        repository_name=repo_handle.repository_name,
        pipeline_name=job_name,
        asset_selection=run_request.asset_selection,
        solid_selection=None,
    )
    external_pipeline = repo_location.get_external_pipeline(pipeline_selector)

    external_execution_plan = repo_location.get_external_execution_plan(
        external_pipeline,
        {},
        DEFAULT_MODE_NAME,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )

    if not run_request.asset_selection:
        check.failed("Expected RunRequest to have an asset selection")

    run = instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=external_pipeline.name,
        run_id=None,
        solids_to_execute=None,
        solid_selection=None,
        run_config={},
        mode=DEFAULT_MODE_NAME,
        step_keys_to_execute=None,
        tags=run_request.tags,
        root_run_id=None,
        parent_run_id=None,
        status=DagsterRunStatus.NOT_STARTED,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
        asset_selection=frozenset(run_request.asset_selection),
    )

    instance.submit_run(run.run_id, workspace)


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
) -> Iterable[Optional[AssetBackfillIterationResult]]:
    """
    Core logic of a backfill iteration. Has no side effects.

    Computes which runs should be requested, if any, as well as updated bookkeeping about the status
    of asset partitions targeted by the backfill.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    instance_queryer = CachingInstanceQueryer(instance=instance)

    initial_candidates: Set[AssetKeyPartitionKey] = set()
    request_roots = not asset_backfill_data.requested_runs_for_target_roots
    if request_roots:
        initial_candidates.update(asset_backfill_data.get_target_root_asset_partitions())

        next_latest_storage_id = instance_queryer.get_latest_storage_id(
            DagsterEventType.ASSET_MATERIALIZATION
        )
        updated_materialized_subset = AssetGraphSubset(asset_graph)
        failed_and_downstream_subset = AssetGraphSubset(asset_graph)
    else:
        (
            parent_materialized_asset_partitions,
            next_latest_storage_id,
        ) = find_parent_materialized_asset_partitions(
            asset_graph=asset_graph,
            instance_queryer=instance_queryer,
            target_asset_selection=AssetSelection.keys(
                *asset_backfill_data.target_subset.asset_keys
            ),
            latest_storage_id=asset_backfill_data.latest_storage_id,
        )
        initial_candidates.update(parent_materialized_asset_partitions)

        yield None

        recently_materialized_asset_partitions = AssetGraphSubset(asset_graph)
        for asset_key in asset_backfill_data.target_subset.asset_keys:
            records = instance_queryer.get_materialization_records(
                asset_key=asset_key, after_cursor=asset_backfill_data.latest_storage_id
            )
            records_in_backfill = [
                record
                for record in records
                if instance_queryer.run_has_tag(
                    run_id=record.run_id, tag_key=BACKFILL_ID_TAG, tag_value=backfill_id
                )
            ]
            recently_materialized_asset_partitions |= {
                AssetKeyPartitionKey(asset_key, record.partition_key)
                for record in records_in_backfill
            }

            yield None

        updated_materialized_subset = (
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

        yield None

    asset_partitions_to_request = asset_graph.bfs_filter_asset_partitions(
        lambda unit, visited: should_backfill_atomic_asset_partitions_unit(
            candidates_unit=unit,
            asset_partitions_to_request=visited,
            asset_graph=asset_graph,
            materialized_subset=updated_materialized_subset,
            target_subset=asset_backfill_data.target_subset,
            failed_and_downstream_subset=failed_and_downstream_subset,
        ),
        initial_asset_partitions=initial_candidates,
    )

    run_requests = build_run_requests(
        asset_partitions_to_request, asset_graph, {BACKFILL_ID_TAG: backfill_id}
    )

    if request_roots:
        check.invariant(
            len(run_requests) > 0,
            "At least one run should be requested on first backfill iteration",
        )

    updated_asset_backfill_data = AssetBackfillData(
        target_subset=asset_backfill_data.target_subset,
        latest_storage_id=next_latest_storage_id or asset_backfill_data.latest_storage_id,
        requested_runs_for_target_roots=asset_backfill_data.requested_runs_for_target_roots
        or request_roots,
        materialized_subset=updated_materialized_subset,
        failed_and_downstream_subset=failed_and_downstream_subset,
        requested_subset=asset_backfill_data.requested_subset | asset_partitions_to_request,
    )
    yield AssetBackfillIterationResult(run_requests, updated_asset_backfill_data)


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
