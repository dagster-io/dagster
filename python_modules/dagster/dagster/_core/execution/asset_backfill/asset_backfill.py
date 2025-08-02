import logging
import os
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, cast

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.assets.graph.remote_asset_graph import (
    RemoteAssetGraph,
    RemoteWorkspaceAssetGraph,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.subset import PartitionsSubset, TimeWindowPartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.errors import (
    DagsterAssetBackfillDataLoadError,
    DagsterDefinitionChangedDeserializationError,
)
from dagster._core.execution.asset_backfill.asset_backfill_data import (
    AssetBackfillComputationData,
    AssetBackfillData,
)
from dagster._core.execution.asset_backfill.asset_backfill_evaluator import (
    AssetBackfillEvaluator,
    AssetBackfillIterationResult,
)
from dagster._core.execution.submit_asset_runs import submit_asset_run
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import NOT_FINISHED_STATUSES, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG, WILL_RETRY_TAG
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._time import datetime_from_timestamp, get_current_timestamp
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

if TYPE_CHECKING:
    from dagster._core.execution.backfill import PartitionBackfill


def get_asset_backfill_run_chunk_size():
    return int(os.getenv("DAGSTER_ASSET_BACKFILL_RUN_CHUNK_SIZE", "25"))


def _get_unloadable_location_names(
    context: BaseWorkspaceRequestContext, logger: logging.Logger
) -> Sequence[str]:
    location_entries_by_name = {
        location_entry.origin.location_name: location_entry
        for location_entry in context.get_code_location_entries().values()
    }
    unloadable_location_names = []

    for location_name, location_entry in location_entries_by_name.items():
        if location_entry.load_error:
            logger.warning(
                f"Failure loading location {location_name} due to error:"
                f" {location_entry.load_error}"
            )
            unloadable_location_names.append(location_name)

    return unloadable_location_names


def _write_updated_backfill_data(
    instance: DagsterInstance,
    backfill_id: str,
    updated_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    updated_run_requests: Sequence[RunRequest],
    updated_reserved_run_ids: Sequence[str],
):
    backfill = check.not_none(instance.get_backfill(backfill_id))
    updated_backfill = backfill.with_asset_backfill_data(
        updated_backfill_data,
        dynamic_partitions_store=instance,
        asset_graph=asset_graph,
    ).with_submitting_run_requests(
        updated_run_requests,
        updated_reserved_run_ids,
    )
    instance.update_backfill(updated_backfill)
    return updated_backfill


async def _submit_runs_and_update_backfill_in_chunks(
    asset_graph_view: AssetGraphView,
    workspace_process_context: IWorkspaceProcessContext,
    backfill_id: str,
    asset_backfill_iteration_result: AssetBackfillIterationResult,
    logger: logging.Logger,
    run_tags: Mapping[str, str],
) -> None:
    from dagster._core.execution.backfill import BulkActionStatus
    from dagster._daemon.utils import DaemonErrorCapture

    asset_graph = cast("RemoteWorkspaceAssetGraph", asset_graph_view.asset_graph)
    instance = asset_graph_view.instance

    run_requests = asset_backfill_iteration_result.run_requests

    # Iterate through runs to request, submitting runs in chunks.
    # In between each chunk, check that the backfill is still marked as 'requested',
    # to ensure that no more runs are requested if the backfill is marked as canceled/canceling.

    updated_backfill_data = asset_backfill_iteration_result.backfill_data

    num_submitted = 0

    reserved_run_ids = asset_backfill_iteration_result.reserved_run_ids

    run_request_execution_data_cache = {}

    chunk_size = get_asset_backfill_run_chunk_size()

    for run_request_idx, run_request in enumerate(run_requests):
        run_id = reserved_run_ids[run_request_idx] if reserved_run_ids else None
        try:
            # create a new request context for each run in case the code location server
            # is swapped out in the middle of the submission process
            workspace = workspace_process_context.create_request_context()
            await submit_asset_run(
                run_id,
                run_request._replace(
                    tags={
                        **run_request.tags,
                        **run_tags,
                        BACKFILL_ID_TAG: backfill_id,
                    }
                ),
                run_request_idx,
                instance,
                workspace_process_context,
                workspace,
                run_request_execution_data_cache,
                {},
                logger,
            )
        except Exception:
            DaemonErrorCapture.process_exception(
                sys.exc_info(),
                logger=logger,
                log_message="Error while submitting run - updating the backfill data before re-raising",
            )
            # Write the runs that we submitted before hitting an error
            _write_updated_backfill_data(
                instance,
                backfill_id,
                updated_backfill_data,
                asset_graph,
                run_requests[num_submitted:],
                asset_backfill_iteration_result.reserved_run_ids[num_submitted:],
            )
            raise

        num_submitted += 1

        updated_backfill_data: AssetBackfillData = (
            updated_backfill_data.with_run_requests_submitted(
                [run_request],
                asset_graph_view,
            )
        )

        # After each chunk or on the final request, write the updated backfill data
        # and check to make sure we weren't interrupted
        if (num_submitted % chunk_size == 0) or num_submitted == len(run_requests):
            backfill = _write_updated_backfill_data(
                instance,
                backfill_id,
                updated_backfill_data,
                asset_graph,
                run_requests[num_submitted:],
                asset_backfill_iteration_result.reserved_run_ids[num_submitted:],
            )

            if backfill.status != BulkActionStatus.REQUESTED:
                break

    return


def _check_target_partitions_subset_is_valid(
    asset_key: AssetKey,
    asset_graph: BaseAssetGraph,
    target_partitions_subset: Optional[PartitionsSubset],
    instance_queryer: CachingInstanceQueryer,
) -> None:
    """Checks for any partitions definition changes since backfill launch that should mark
    the backfill as failed.
    """
    if not asset_graph.has(asset_key):
        raise DagsterDefinitionChangedDeserializationError(
            f"Asset {asset_key} existed at storage-time, but no longer does"
        )

    partitions_def = asset_graph.get(asset_key).partitions_def

    if target_partitions_subset:  # Asset was partitioned at storage time
        if partitions_def is None:
            raise DagsterDefinitionChangedDeserializationError(
                f"Asset {asset_key} had a PartitionsDefinition at storage-time, but no longer does"
            )

        # If the asset was time-partitioned at storage time but the time partitions def
        # has changed, mark the backfill as failed
        if isinstance(
            target_partitions_subset, TimeWindowPartitionsSubset
        ) and target_partitions_subset.partitions_def.get_serializable_unique_identifier(
            instance_queryer
        ) != partitions_def.get_serializable_unique_identifier(instance_queryer):
            raise DagsterDefinitionChangedDeserializationError(
                f"This partitions definition for asset {asset_key} has changed since this backfill"
                " was stored. Changing the partitions definition for a time-partitioned "
                "asset during a backfill is not supported."
            )

        else:
            # Check that all target partitions still exist. If so, the backfill can continue.a
            existent_partitions_subset = (
                partitions_def.subset_with_all_partitions() & target_partitions_subset
            )
            removed_partitions_subset = target_partitions_subset - existent_partitions_subset
            if len(removed_partitions_subset) > 0:
                raise DagsterDefinitionChangedDeserializationError(
                    f"Targeted partitions for asset {asset_key} have been removed since this backfill was stored. "
                    f"The following partitions were removed: {removed_partitions_subset.get_partition_keys()}"
                )

    else:  # Asset unpartitioned at storage time
        if partitions_def is not None:
            raise DagsterDefinitionChangedDeserializationError(
                f"Asset {asset_key} was not partitioned at storage-time, but is now"
            )


def _check_validity_and_deserialize_asset_backfill_data(
    workspace_context: BaseWorkspaceRequestContext,
    backfill: "PartitionBackfill",
    asset_graph: RemoteWorkspaceAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    logger: logging.Logger,
) -> Optional[AssetBackfillData]:
    """Attempts to deserialize asset backfill data. If the asset backfill data is valid,
    returns the deserialized data, else returns None.
    """
    unloadable_locations = _get_unloadable_location_names(workspace_context, logger)

    try:
        asset_backfill_data = backfill.get_asset_backfill_data(asset_graph)
        for asset_key in asset_backfill_data.target_subset.asset_keys:
            _check_target_partitions_subset_is_valid(
                asset_key,
                asset_graph,
                asset_backfill_data.target_subset.get_partitions_subset(asset_key)
                if asset_key in asset_backfill_data.target_subset.partitions_subsets_by_asset_key
                else None,
                instance_queryer,
            )
    except DagsterDefinitionChangedDeserializationError as ex:
        unloadable_locations_error = (
            "This could be because it's inside a code location that's failing to load:"
            f" {unloadable_locations}"
            if unloadable_locations
            else ""
        )
        if (
            os.environ.get("DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR")
            and unloadable_locations
        ):
            logger.warning(
                f"Backfill {backfill.backfill_id} was unable to continue due to a missing asset or"
                " partition in the asset graph. The backfill will resume once it is available"
                f" again.\n{ex}. {unloadable_locations_error}"
            )
            return None
        else:
            raise DagsterAssetBackfillDataLoadError(f"{ex}. {unloadable_locations_error}")

    return asset_backfill_data


def backfill_is_complete(
    backfill_id: str,
    backfill_data: AssetBackfillData,
    instance: DagsterInstance,
    logger: logging.Logger,
):
    """A backfill is complete when:
    1. all asset partitions in the target subset have a materialization state (successful, failed, downstream of a failed partition).
    2. there are no in progress runs for the backfill.
    3. there are no failed runs that will result in an automatic retry, but have not yet been retried.

    Condition 1 ensures that for each asset partition we have attempted to materialize it or have determined we
    cannot materialize it because of a failed dependency. Condition 2 ensures that no retries of failed runs are
    in progress. Condition 3 guards against a race condition where a failed run could be automatically retried
    but it was not added into the queue in time to be caught by condition 2.

    Since the AssetBackfillData object stores materialization states per asset partition, we want to ensure the
    daemon continues to update the backfill data until all runs have finished in order to display the
    final partition statuses in the UI.
    """
    # Condition 1 - if any asset partitions in the target subset do not have a materialization state, the backfill
    # is not complete
    if not backfill_data.all_targeted_partitions_have_materialization_status():
        logger.info(
            "Not all targeted asset partitions have a materialization status. Backfill is still in progress."
        )
        return False
    # Condition 2 - if there are in progress runs for the backfill, the backfill is not complete
    if (
        len(
            instance.get_run_ids(
                filters=RunsFilter(
                    statuses=NOT_FINISHED_STATUSES,
                    tags={BACKFILL_ID_TAG: backfill_id},
                ),
                limit=1,
            )
        )
        > 0
    ):
        logger.info("Backfill has in progress runs. Backfill is still in progress.")
        return False
    # Condition 3 - if there are runs that will be retried, but have not yet been retried, the backfill is not complete
    runs_waiting_to_retry = [
        run.run_id
        for run in instance.get_runs(
            filters=RunsFilter(
                tags={BACKFILL_ID_TAG: backfill_id, WILL_RETRY_TAG: "true"},
                statuses=[DagsterRunStatus.FAILURE],
            )
        )
        if run.is_complete_and_waiting_to_retry
    ]
    if len(runs_waiting_to_retry) > 0:
        num_runs_to_log = 20
        formatted_runs = "\n".join(runs_waiting_to_retry[:num_runs_to_log])
        if len(runs_waiting_to_retry) > num_runs_to_log:
            formatted_runs += f"\n... {len(runs_waiting_to_retry) - num_runs_to_log} more"
        logger.info(
            f"The following runs for the backfill will be retried, but retries have not been launched. Backfill is still in progress:\n{formatted_runs}"
        )
        return False
    return True


async def execute_asset_backfill_iteration(
    backfill: "PartitionBackfill",
    logger: logging.Logger,
    workspace_process_context: IWorkspaceProcessContext,
    instance: DagsterInstance,
) -> None:
    """Runs an iteration of the backfill, including submitting runs and updating the backfill object
    in the DB.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill

    logger.info(f"Evaluating asset backfill {backfill.backfill_id}")

    workspace_context = workspace_process_context.create_request_context()
    asset_graph = workspace_context.asset_graph

    if not backfill.is_asset_backfill:
        check.failed("Backfill must be an asset backfill")

    backfill_start_datetime = datetime_from_timestamp(backfill.backfill_timestamp)

    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=backfill_start_datetime,
            last_event_id=None,
        ),
        instance=instance,
        asset_graph=asset_graph,
    )

    instance_queryer = asset_graph_view.get_inner_queryer_for_back_compat()

    previous_asset_backfill_data = _check_validity_and_deserialize_asset_backfill_data(
        workspace_context, backfill, asset_graph, instance_queryer, logger
    )
    if previous_asset_backfill_data is None:
        return
    previous_data = previous_asset_backfill_data.get_computation_data(
        asset_graph_view, backfill.backfill_id
    )

    logger.info(
        f"Assets targeted by backfill {backfill.backfill_id} are valid. Continuing execution with current status: {backfill.status}."
    )

    if backfill.status == BulkActionStatus.REQUESTED:
        if backfill.submitting_run_requests:
            # interrupted in the middle of executing run requests - re-construct the in-progress iteration result
            logger.warn(
                f"Resuming previous backfill iteration and re-submitting {len(backfill.submitting_run_requests)} runs."
            )
            result = AssetBackfillIterationResult(
                run_requests=backfill.submitting_run_requests,
                backfill_data=previous_asset_backfill_data,
                reserved_run_ids=backfill.reserved_run_ids,
            )

            updated_backfill = backfill
        else:
            # Generate a new set of run requests to launch, and update the materialized and failed
            # subsets
            result = AssetBackfillEvaluator(previous_data=previous_data, logger=logger).evaluate()

            # Write the updated asset backfill data with in progress run requests before we launch anything, for idempotency
            # Make sure we didn't get canceled in the interim
            updated_backfill: PartitionBackfill = check.not_none(
                instance.get_backfill(backfill.backfill_id)
            )
            if updated_backfill.status != BulkActionStatus.REQUESTED:
                logger.info("Backfill was canceled mid-iteration, returning")
                return

            updated_backfill = (
                updated_backfill.with_asset_backfill_data(
                    result.backfill_data,
                    dynamic_partitions_store=instance,
                    asset_graph=asset_graph,
                )
                .with_submitting_run_requests(result.run_requests, result.reserved_run_ids)
                .with_failure_count(0)
            )

            instance.update_backfill(updated_backfill)

        if result.run_requests:
            await _submit_runs_and_update_backfill_in_chunks(
                asset_graph_view,
                workspace_process_context,
                updated_backfill.backfill_id,
                result,
                logger,
                run_tags=updated_backfill.tags,
            )

        updated_backfill = cast(
            "PartitionBackfill", instance.get_backfill(updated_backfill.backfill_id)
        )
        if updated_backfill.status == BulkActionStatus.REQUESTED:
            check.invariant(
                not updated_backfill.submitting_run_requests,
                "All run requests should have been submitted",
            )

        updated_backfill_data = updated_backfill.get_asset_backfill_data(asset_graph)

        if backfill_is_complete(
            backfill_id=backfill.backfill_id,
            backfill_data=updated_backfill_data,
            instance=instance,
            logger=logger,
        ):
            if (
                updated_backfill_data.failed_and_downstream_subset.num_partitions_and_non_partitioned_assets
                > 0
            ):
                updated_backfill = updated_backfill.with_status(BulkActionStatus.COMPLETED_FAILED)
            else:
                updated_backfill: PartitionBackfill = updated_backfill.with_status(
                    BulkActionStatus.COMPLETED_SUCCESS
                )

            updated_backfill = updated_backfill.with_end_timestamp(get_current_timestamp())
            instance.update_backfill(updated_backfill)

        logger.info(
            f"Asset backfill {updated_backfill.backfill_id} completed iteration with status {updated_backfill.status}."
        )
        _log_summary(
            previous_data,
            updated_backfill_data.get_computation_data(asset_graph_view, backfill.backfill_id),
            logger,
        )

    elif backfill.status == BulkActionStatus.CANCELING:
        from dagster._core.execution.backfill import cancel_backfill_runs_and_cancellation_complete

        all_runs_canceled = cancel_backfill_runs_and_cancellation_complete(
            instance=instance, backfill_id=backfill.backfill_id
        )

        # Update the asset backfill data to contain the newly materialized/failed partitions.
        evaluator = AssetBackfillEvaluator(previous_data=previous_data)
        updated_asset_backfill_data = evaluator.evaluate_cancellation()

        # Refetch, in case the backfill was forcibly marked as canceled in the meantime
        backfill = cast("PartitionBackfill", instance.get_backfill(backfill.backfill_id))
        updated_backfill: PartitionBackfill = backfill.with_asset_backfill_data(
            updated_asset_backfill_data,
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        )
        # The asset backfill is successfully canceled when all requested runs have finished (success,
        # failure, or cancellation). Since the AssetBackfillData object stores materialization states
        # per asset partition, the daemon continues to update the backfill data until all runs have
        # finished in order to display the final partition statuses in the UI.
        all_partitions_marked_completed = (
            updated_asset_backfill_data.all_requested_partitions_marked_as_materialized_or_failed()
        )
        if all_partitions_marked_completed:
            updated_backfill = updated_backfill.with_status(
                BulkActionStatus.CANCELED
            ).with_end_timestamp(get_current_timestamp())

        if all_runs_canceled and not all_partitions_marked_completed:
            logger.warning(
                "All runs have completed, but not all requested partitions have been marked as materialized or failed. "
                "This may indicate that some runs succeeded without materializing their expected partitions."
            )
            updated_backfill = updated_backfill.with_status(
                BulkActionStatus.CANCELED
            ).with_end_timestamp(get_current_timestamp())

        instance.update_backfill(updated_backfill)

        logger.info(
            f"Asset backfill {backfill.backfill_id} completed cancellation iteration with status {updated_backfill.status}."
        )
        logger.debug(
            f"Updated asset backfill data after cancellation iteration: {updated_asset_backfill_data}"
        )
    elif backfill.status == BulkActionStatus.CANCELED:
        # The backfill was forcibly canceled, skip iteration
        pass
    else:
        check.failed(f"Unexpected backfill status: {backfill.status}")


def _log_summary(
    previous_data: AssetBackfillComputationData,
    updated_data: AssetBackfillComputationData,
    logger: logging.Logger,
) -> None:
    new_materialized_partitions = updated_data.materialized_subset.compute_difference(
        previous_data.materialized_subset
    )
    new_failed_partitions = updated_data.failed_and_downstream_subset.compute_difference(
        previous_data.failed_and_downstream_subset
    )
    updated_backfill_in_progress = updated_data.requested_subset.compute_difference(
        updated_data.materialized_subset.compute_union(updated_data.failed_and_downstream_subset)
    )
    previous_backfill_in_progress = updated_data.requested_subset.compute_difference(
        updated_data.materialized_subset
    )
    new_requested_partitions = updated_backfill_in_progress.compute_difference(
        previous_backfill_in_progress
    )
    logger.info(
        "Backfill iteration summary:\n"
        f"**Assets materialized since last iteration:**\n{str(new_materialized_partitions) if not new_materialized_partitions.is_empty else 'None'}\n"
        f"**Assets failed since last iteration and their downstream assets:**\n{str(new_failed_partitions) if not new_failed_partitions.is_empty else 'None'}\n"
        f"**Assets requested by this iteration:**\n{str(new_requested_partitions) if not new_requested_partitions.is_empty else 'None'}\n"
    )
    logger.info(
        "Overall backfill status:\n"
        f"**Materialized assets:**\n{str(updated_data.materialized_subset) if not updated_data.materialized_subset.is_empty else 'None'}\n"
        f"**Failed assets and their downstream assets:**\n{str(updated_data.failed_and_downstream_subset) if not updated_data.failed_and_downstream_subset.is_empty else 'None'}\n"
        f"**Assets requested or in progress:**\n{str(updated_backfill_in_progress) if not updated_backfill_in_progress.is_empty else 'None'}\n"
    )
    logger.debug(f"Updated asset backfill data for {updated_data.backfill_id}: {updated_data}")
