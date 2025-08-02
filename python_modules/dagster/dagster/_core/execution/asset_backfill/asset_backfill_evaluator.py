import logging
import os
import time
from collections.abc import Sequence
from typing import Optional, cast

from dagster_shared.record import record

from dagster._core.asset_graph_view.asset_graph_subset_view import AssetGraphSubsetView
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import EntitySubsetValue
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.remote_asset_graph import RemoteWorkspaceAssetGraph
from dagster._core.definitions.automation_tick_evaluation_context import (
    build_run_requests_with_backfill_policies,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import (
    PartitionLoadingContext,
    use_partition_loading_context,
)
from dagster._core.definitions.partitions.mapping import (
    IdentityPartitionMapping,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.execution.asset_backfill.asset_backfill_data import (
    AssetBackfillComputationData,
    AssetBackfillData,
)
from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.utils import make_new_run_id

MATERIALIZATION_CHUNK_SIZE = int(
    os.getenv("DAGSTER_ASSET_BACKFILL_MATERIALIZATION_CHUNK_SIZE", "1000")
)


@record
class AssetBackfillComputationResult:
    """Represents the result of a backfill computation. Contains information about the subset of
    the asset that should be backfilled this tick, and reasons why unselected subsets will not be
    backfilled on this tick.
    """

    to_request: EntitySubset[AssetKey]
    rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]]


@record
class AssetBackfillIterationResult:
    run_requests: Sequence[RunRequest]
    backfill_data: AssetBackfillData
    reserved_run_ids: Sequence[str]


class AssetBackfillEvaluator:
    """Object that evaluates an iteration of an asset backfill."""

    def __init__(
        self,
        previous_data: AssetBackfillComputationData,
        logger: Optional[logging.Logger] = None,
    ):
        self.previous_data = previous_data
        self.logger = logger or logging.getLogger("AssetBackfillEvaluator")

    @property
    def view(self) -> AssetGraphView:
        return self.previous_data.view

    @property
    def _partition_loading_context(self) -> PartitionLoadingContext:
        return self.view._partition_loading_context  # noqa

    def _log_results(
        self,
        to_request_subset: AssetGraphSubsetView[AssetKey],
        rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]],
    ):
        self.logger.info(
            f"Asset partitions to request:\n{to_request_subset!s}"
            if not to_request_subset.is_empty
            else "No asset partitions to request."
        )

        if len(rejected_subsets_with_reasons) > 0:
            not_requested_str = "\n\n".join(
                [
                    f"{asset_graph_subset!s}\nReason: {reason}"
                    for asset_graph_subset, reason in rejected_subsets_with_reasons
                ]
            )
            self.logger.info(
                f"The following assets were considered for materialization but not requested:\n\n{not_requested_str}"
            )

    def _get_updated_materialized_subset(self) -> AssetGraphSubsetView[AssetKey]:
        """Returns the partitions that have been materialized by the backfill.

        This function is a generator so we can return control to the daemon and let it heartbeat
        during expensive operations.
        """
        recently_materialized_asset_partitions = AssetGraphSubsetView.empty(self.view)
        for asset_key in self.previous_data.target_subset.keys:
            cursor = None
            has_more = True
            while has_more:
                materializations_result = self.view.instance.fetch_materializations(
                    AssetRecordsFilter(
                        asset_key=asset_key, after_storage_id=self.previous_data.latest_storage_id
                    ),
                    cursor=cursor,
                    limit=MATERIALIZATION_CHUNK_SIZE,
                )

                cursor = materializations_result.cursor
                has_more = materializations_result.has_more

                run_ids = [
                    record.run_id for record in materializations_result.records if record.run_id
                ]
                if run_ids:
                    run_records = self.view.instance.get_run_records(
                        filters=RunsFilter(run_ids=run_ids),
                    )
                    run_ids_in_backfill = {
                        run_record.dagster_run.run_id
                        for run_record in run_records
                        if run_record.dagster_run.tags.get(BACKFILL_ID_TAG)
                        == self.previous_data.backfill_id
                    }

                    materialization_records_in_backfill = [
                        record
                        for record in materializations_result.records
                        if record.run_id in run_ids_in_backfill
                    ]
                    materialized_for_run = AssetGraphSubsetView.from_asset_partitions(
                        self.view,
                        {
                            AssetKeyPartitionKey(asset_key, record.partition_key)
                            for record in materialization_records_in_backfill
                        },
                    )
                    recently_materialized_asset_partitions = (
                        recently_materialized_asset_partitions.compute_union(materialized_for_run)
                    )

        return self.previous_data.materialized_subset.compute_union(
            recently_materialized_asset_partitions
        )

    def _get_updated_failed_asset_graph_subset(
        self, updated_materialized_subset: AssetGraphSubsetView[AssetKey]
    ) -> AssetGraphSubsetView[AssetKey]:
        """Returns asset subset that materializations were requested for as part of the backfill, but were
        not successfully materialized.

        This function gets a list of all runs for the backfill that have failed and extracts the asset partitions
        that were not materialized from those runs. However, we need to account for retried runs. If a run was
        successfully retried, the original failed run will still be processed in this function. So we check the
        failed asset partitions against the list of successfully materialized asset partitions. If an asset partition
        is in the materialized_subset, it means the failed run was retried and the asset partition was materialized.

        Includes canceled asset partitions. Implementation assumes that successful runs won't have any
        failed partitions.
        """
        runs = self.view.instance.get_runs(
            filters=RunsFilter(
                tags={BACKFILL_ID_TAG: self.previous_data.backfill_id},
                statuses=[DagsterRunStatus.CANCELED, DagsterRunStatus.FAILURE],
            )
        )

        result: AssetGraphSubsetView[AssetKey] = AssetGraphSubsetView.empty(self.view)
        instance_queryer = self.view.get_inner_queryer_for_back_compat()
        for run in runs:
            planned_asset_keys = instance_queryer.get_planned_materializations_for_run(
                run_id=run.run_id
            )
            completed_asset_keys = instance_queryer.get_current_materializations_for_run(
                run_id=run.run_id
            )
            failed_asset_keys = planned_asset_keys - completed_asset_keys

            if (
                run.tags.get(ASSET_PARTITION_RANGE_START_TAG)
                and run.tags.get(ASSET_PARTITION_RANGE_END_TAG)
                and run.tags.get(PARTITION_NAME_TAG) is None
            ):
                # reconstruct the partition keys from a chunked backfill run
                partition_range = PartitionKeyRange(
                    start=run.tags[ASSET_PARTITION_RANGE_START_TAG],
                    end=run.tags[ASSET_PARTITION_RANGE_END_TAG],
                )
                candidate_subset = AssetGraphSubsetView(
                    asset_graph_view=self.view,
                    subsets=[
                        self.view.get_entity_subset_in_range(asset_key, partition_range)
                        for asset_key in failed_asset_keys
                    ],
                )

            else:
                # a regular backfill run that run on a single partition
                partition_key = run.tags.get(PARTITION_NAME_TAG)
                candidate_subset = AssetGraphSubsetView.from_asset_partitions(
                    self.view,
                    {
                        AssetKeyPartitionKey(asset_key, partition_key)
                        for asset_key in failed_asset_keys
                    },
                )

            asset_subset_still_failed = candidate_subset.compute_difference(
                updated_materialized_subset
            )
            result = result.compute_union(asset_subset_still_failed)

        return result

    def _get_updated_data(self) -> AssetBackfillComputationData:
        """Returns the AssetBackfillComputationData for the current iteration. This will include updated
        failed and materialized subsets.
        """
        # Events are not always guaranteed to be written to the event log in monotonically increasing
        # order, so add a configurable offset to ensure that any stragglers will still be included in
        # the next iteration.
        # This may result in the same event being considered within multiple iterations, but
        # idempotence checks later ensure that the materialization isn't incorrectly
        # double-counted.
        cursor_offset = int(os.getenv("ASSET_BACKFILL_CURSOR_OFFSET", "0"))
        next_latest_storage_id = (
            self.previous_data.view.instance.event_log_storage.get_maximum_record_id() or 0
        )
        next_latest_storage_id = max(next_latest_storage_id - cursor_offset, 0)

        cursor_delay_time = int(os.getenv("ASSET_BACKFILL_CURSOR_DELAY_TIME", "0"))
        # Events are not guaranteed to be written to the event log in monotonic increasing order,
        # so we wait to ensure all events up until next_latest_storage_id have been written.
        if cursor_delay_time:
            time.sleep(cursor_delay_time)

        updated_materialized_subset = self._get_updated_materialized_subset()
        updated_failed_subset = self._get_updated_failed_asset_graph_subset(
            updated_materialized_subset
        )

        materialized_since_last_tick = updated_materialized_subset.compute_difference(
            self.previous_data.materialized_subset
        )
        self.logger.info(
            f"Assets materialized since last tick:\n{materialized_since_last_tick!s}"
            if not materialized_since_last_tick.is_empty
            else "No relevant assets materialized since last tick."
        )

        return AssetBackfillComputationData(
            view=self.previous_data.view,
            latest_storage_id=next_latest_storage_id,
            backfill_start_timestamp=self.previous_data.backfill_start_timestamp,
            backfill_id=self.previous_data.backfill_id,
            target_subset=self.previous_data.target_subset,
            requested_subset=self.previous_data.requested_subset,
            materialized_subset=updated_materialized_subset,
            failed_and_downstream_subset=updated_failed_subset.compute_downstream_subset(),
        )

    def _get_cant_run_with_parent_reason(
        self,
        data: AssetBackfillComputationData,
        candidate_subset: EntitySubset[AssetKey],
        parent_subset: EntitySubset[AssetKey],
        to_request_subset: AssetGraphSubsetView[AssetKey],
    ) -> Optional[str]:
        candidate_key = candidate_subset.key
        parent_key = parent_subset.key

        assert isinstance(data.view.asset_graph, RemoteWorkspaceAssetGraph)
        asset_graph = cast("RemoteWorkspaceAssetGraph", data.view.asset_graph)

        parent_node = asset_graph.get(parent_key)
        candidate_node = asset_graph.get(candidate_key)
        partition_mapping = asset_graph.get_partition_mapping(
            candidate_key, parent_asset_key=parent_key
        )

        # First filter out cases where even if the parent was requested this iteration, it wouldn't
        # matter, because the parent and child can't execute in the same run

        # checks if there is a simple partition mapping between the parent and the child
        has_identity_partition_mapping = (
            # both unpartitioned
            (not candidate_node.is_partitioned and not parent_node.is_partitioned)
            # normal identity partition mapping
            or isinstance(partition_mapping, IdentityPartitionMapping)
            # for assets with the same time partitions definition, a non-offset partition
            # mapping functions as an identity partition mapping
            or (
                isinstance(partition_mapping, TimeWindowPartitionMapping)
                and partition_mapping.start_offset == 0
                and partition_mapping.end_offset == 0
            )
        )
        if parent_node.backfill_policy != candidate_node.backfill_policy:
            return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different backfill policies so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key} is materialized."

        if (
            parent_node.resolve_to_singular_repo_scoped_node().repository_handle
            != candidate_node.resolve_to_singular_repo_scoped_node().repository_handle
        ):
            return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} are in different code locations so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."

        if parent_node.partitions_def != candidate_node.partitions_def:
            return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different partitions definitions so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."

        parent_target_subset = data.target_subset.get(parent_key)
        candidate_target_subset = data.target_subset.get(candidate_key)

        num_parent_partitions_being_requested_this_tick = parent_target_subset.size

        is_self_dependency = parent_key == candidate_key

        has_self_dependency = any(
            parent_key == candidate_key for parent_key in candidate_node.parent_keys
        )

        # launching a self-dependant asset with a non-self-dependant asset can result in invalid
        # runs being launched that don't respect lineage
        if (
            has_self_dependency
            and parent_key not in candidate_node.execution_set_asset_keys
            and num_parent_partitions_being_requested_this_tick > 0
        ):
            return "Self-dependant assets cannot be materialized in the same run as other assets."

        if not (
            # this check is here to guard against cases where the parent asset has a superset of
            # the child asset's asset partitions, which will mean that the runs that would be created
            # would not combine the parent and child assets into a single run. this is not relevant
            # for self-dependencies, because the parent and child are the same asset.
            is_self_dependency
            or (
                # in the typical case, we will only allow this candidate subset to be requested if
                # it contains exactly the same partitions as its parent asset for this evaluation,
                # otherwise they may end up in different runs
                to_request_subset.get(parent_key).get_internal_value()
                == candidate_subset.get_internal_value()
            )
        ):
            return (
                f"parent {parent_node.key.to_user_string()} is requesting a different set of partitions from "
                f"{candidate_node.key.to_user_string()}, meaning they cannot be grouped together in the same run."
            )

        if is_self_dependency:
            if parent_node.backfill_policy is None:
                required_parent_subset = parent_subset
            else:
                # with a self dependency, all of its parent partitions need to either have already
                # been materialized or be in the candidate subset
                required_parent_subset = parent_subset.compute_difference(
                    candidate_subset
                ).compute_difference(data.materialized_subset.get(parent_key))

            if not required_parent_subset.is_empty:
                return f"Waiting for the following parent partitions of a self-dependant asset to materialize: {required_parent_subset!s}"
            else:
                return None

        if not (
            # if there is a simple mapping between the parent and the child, then
            # with the parent
            has_identity_partition_mapping
            # if there is not a simple mapping, we can only materialize this asset with its
            # parent if...
            or (
                # there is a backfill policy for the parent
                parent_node.backfill_policy is not None
                # the same subset of parents is targeted as the child
                and parent_target_subset.get_internal_value()
                == candidate_target_subset.get_internal_value()
                and (
                    # there is no limit on the size of a single run or...
                    parent_node.backfill_policy.max_partitions_per_run is None
                    # a single run can materialize all requested parent partitions
                    or parent_node.backfill_policy.max_partitions_per_run
                    > num_parent_partitions_being_requested_this_tick
                )
                # all targeted parents are being requested this tick
                and num_parent_partitions_being_requested_this_tick == parent_target_subset.size
            )
        ):
            failed_reason = (
                f"partition mapping between {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} is not simple and "
                f"{parent_node.key.to_user_string()} does not meet requirements of: targeting the same partitions as "
                f"{candidate_node.key.to_user_string()}, have all of its partitions requested in this iteration, having "
                "a backfill policy, and that backfill policy size limit is not exceeded by adding "
                f"{candidate_node.key.to_user_string()} to the run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."
            )
            return failed_reason

        return None

    def _evaluate_entity_subset(
        self,
        data: AssetBackfillComputationData,
        candidate_subset: EntitySubset[AssetKey],
        to_request_subset: AssetGraphSubsetView[AssetKey],
    ) -> AssetBackfillComputationResult:
        """Core logic for evaluating a single entity subset.

        Returns a subset of the candidate subset that should be requested, and a list of subsets that
        were rejected with reasons why.
        """
        rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]] = []

        key = candidate_subset.key
        missing_in_target_partitions = candidate_subset.compute_difference(
            data.target_subset.get(key)
        )
        if not missing_in_target_partitions.is_empty:
            # Don't include a failure reason for this subset since it is unlikely to be
            # useful to know that an untargeted subset was not included
            candidate_subset = candidate_subset.compute_difference(missing_in_target_partitions)

        failed_and_downstream_partitions = candidate_subset.compute_intersection(
            data.failed_and_downstream_subset.get(key)
        )
        if not failed_and_downstream_partitions.is_empty:
            # Similar to above, only include a failure reason for 'interesting' failure reasons
            candidate_subset = candidate_subset.compute_difference(failed_and_downstream_partitions)

        materialized_partitions = candidate_subset.compute_intersection(
            data.materialized_subset.get(key)
        )
        if not materialized_partitions.is_empty:
            # Similar to above, only include a failure reason for 'interesting' failure reasons
            candidate_subset = candidate_subset.compute_difference(materialized_partitions)

        requested_partitions = candidate_subset.compute_intersection(to_request_subset.get(key))

        if not requested_partitions.is_empty:
            # Similar to above, only include a failure reason for 'interesting' failure reasons
            candidate_subset = candidate_subset.compute_difference(requested_partitions)

        parent_keys = data.view.asset_graph.get(candidate_subset.key).parent_keys
        has_any_parent_being_requested_this_tick = any(
            not to_request_subset.get(parent_key).is_empty for parent_key in parent_keys
        )

        for parent_key in sorted(parent_keys):
            if candidate_subset.is_empty:
                break

            parent_subset, required_but_nonexistent_subset = (
                data.view.compute_parent_subset_and_required_but_nonexistent_subset(
                    parent_key, candidate_subset
                )
            )

            if not required_but_nonexistent_subset.is_empty:
                raise DagsterInvariantViolationError(
                    f"Asset partition subset {candidate_subset}"
                    f" depends on invalid partitions {required_but_nonexistent_subset}"
                )

            parent_materialized_subset = data.materialized_subset.get(parent_key)

            # Children with parents that are targeted but not materialized are eligible
            # to be filtered out if the parent has not run yet
            targeted_but_not_materialized_parent_subset: EntitySubset[AssetKey] = (
                parent_subset.compute_intersection(data.target_subset.get(parent_key))
            ).compute_difference(parent_materialized_subset)

            possibly_waiting_for_parent_subset = (
                targeted_but_not_materialized_parent_subset.compute_child_subset(
                    candidate_subset.key
                )
            ).compute_intersection(candidate_subset)

            if not possibly_waiting_for_parent_subset.is_empty:
                cant_run_with_parent_reason = self._get_cant_run_with_parent_reason(
                    data, candidate_subset, parent_subset, to_request_subset
                )
                is_self_dependency = parent_key == candidate_subset.key

                if cant_run_with_parent_reason is not None:
                    # if any parents are also being requested this tick and there is any reason to
                    # believe that any parent can't be materialized with its child subset, then filter out
                    # the whole child subset for now, to ensure that the parent and child aren't submitted
                    # with different subsets which would incorrectly launch them in different runs
                    # despite the child depending on the parent. Otherwise, we can just filter out the
                    # specific ineligible child keys (to ensure that they aren't required before
                    # their parents materialize)
                    if not is_self_dependency and has_any_parent_being_requested_this_tick:
                        rejected_subsets_with_reasons.append(
                            (
                                candidate_subset.get_internal_value(),
                                cant_run_with_parent_reason,
                            )
                        )
                        candidate_subset = data.view.get_empty_subset(key=candidate_subset.key)
                    else:
                        candidate_subset = candidate_subset.compute_difference(
                            possibly_waiting_for_parent_subset
                        )
                        rejected_subsets_with_reasons.append(
                            (
                                possibly_waiting_for_parent_subset.get_internal_value(),
                                cant_run_with_parent_reason,
                            )
                        )

                if is_self_dependency:
                    self_dependent_node = data.view.asset_graph.get(candidate_subset.key)
                    # ensure that we don't produce more than max_partitions_per_run partitions
                    # if a backfill policy is set
                    if (
                        self_dependent_node.backfill_policy is not None
                        and self_dependent_node.backfill_policy.max_partitions_per_run is not None
                    ):
                        # only the first N partitions can be requested
                        num_allowed_partitions = (
                            self_dependent_node.backfill_policy.max_partitions_per_run
                        )
                        # TODO add a method for paginating through the keys in order
                        # and returning the first N instead of listing all of them
                        # (can't use expensively_compute_asset_partitions because it returns
                        # an unordered set)
                        internal_value = candidate_subset.get_internal_value()
                        partition_keys_to_include = (
                            list(internal_value.get_partition_keys())
                            if isinstance(internal_value, PartitionsSubset)
                            else [None]
                        )[:num_allowed_partitions]
                        partition_subset_to_include = AssetGraphSubset.from_asset_partition_set(
                            {
                                AssetKeyPartitionKey(self_dependent_node.key, partition_key)
                                for partition_key in partition_keys_to_include
                            },
                            asset_graph=data.view.asset_graph,
                        )
                        entity_subset_to_include = (
                            data.view.get_entity_subset_from_asset_graph_subset(
                                partition_subset_to_include, self_dependent_node.key
                            )
                        )

                        rejected_subset = candidate_subset.compute_difference(
                            entity_subset_to_include
                        )

                        if not rejected_subset.is_empty:
                            rejected_subsets_with_reasons.append(
                                (
                                    rejected_subset.get_internal_value(),
                                    "Respecting the maximum number of partitions per run for the backfill policy of a self-dependant asset",
                                )
                            )

                        candidate_subset = entity_subset_to_include

        return AssetBackfillComputationResult(
            to_request=candidate_subset,
            rejected_subsets_with_reasons=rejected_subsets_with_reasons,
        )

    @use_partition_loading_context
    def evaluate(self) -> AssetBackfillIterationResult:
        # query the instance to find any updates to the set of materialized and failed partitions
        updated_data = self._get_updated_data()
        candidate_graph_subset = updated_data.get_candidate_subset()

        self.logger.info(
            f"Considering the following candidate subset:\n{candidate_graph_subset!s}"
            if not candidate_graph_subset.is_empty
            else "Candidate subset is empty."
        )

        # iterate over the keys in topological order, and evaluate the candidates for that
        # key, determining which of the candidates should be requested.
        asset_graph_view = updated_data.view
        to_request_subset = AssetGraphSubsetView.empty(asset_graph_view)
        rejected_subsets_with_reasons = []
        for asset_key in asset_graph_view.asset_graph.toposorted_asset_keys:
            candidate_subset = candidate_graph_subset.get(asset_key)
            if candidate_subset.is_empty:
                continue

            result = self._evaluate_entity_subset(updated_data, candidate_subset, to_request_subset)
            to_request_subset = to_request_subset.compute_union(result.to_request)
            rejected_subsets_with_reasons.extend(result.rejected_subsets_with_reasons)

        self._log_results(to_request_subset, rejected_subsets_with_reasons)

        # construct run requests for the requested partitions
        run_requests = build_run_requests_with_backfill_policies(
            asset_graph=asset_graph_view.asset_graph,
            asset_partitions=set(
                to_request_subset.to_asset_graph_subset().iterate_asset_partitions()
            ),
        )

        return AssetBackfillIterationResult(
            run_requests=run_requests,
            backfill_data=updated_data.to_asset_backfill_data(to_request_subset),
            reserved_run_ids=[make_new_run_id() for _ in range(len(run_requests))],
        )

    def evaluate_cancellation(self) -> AssetBackfillData:
        """For asset backfills in the "canceling" state, fetch the asset backfill data with the updated
        materialized and failed subsets.
        """
        updated_materialized_subset = self._get_updated_materialized_subset()
        failed_subset = self._get_updated_failed_asset_graph_subset(updated_materialized_subset)

        # we fetch the failed_subset to get any new assets that have failed and add that to the set of
        # assets we already know failed and their downstreams. However we need to remove any assets in
        # updated_materialized_subset to account for the case where a run retry successfully
        # materialized a previously failed asset.
        original_failed_subset = self.previous_data.failed_and_downstream_subset
        updated_failed_subset = original_failed_subset.compute_union(failed_subset)
        updated_failed_subset = updated_failed_subset.compute_difference(
            updated_materialized_subset
        )

        return AssetBackfillData(
            target_subset=self.previous_data.target_subset.to_asset_graph_subset(),
            latest_storage_id=self.previous_data.latest_storage_id,
            requested_runs_for_target_roots=True,
            materialized_subset=updated_materialized_subset.to_asset_graph_subset(),
            failed_and_downstream_subset=updated_failed_subset.to_asset_graph_subset(),
            requested_subset=self.previous_data.requested_subset.to_asset_graph_subset(),
            backfill_start_time=TimestampWithTimezone(
                self.previous_data.backfill_start_timestamp, "UTC"
            ),
        )
