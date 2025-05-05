from typing import Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster import AssetKey
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.loader import LoadingContext
from dagster._core.remote_representation.external_data import PartitionsSnap
from dagster._core.storage.dagster_run import RunRecord
from dagster._core.storage.event_log.base import AssetRecord
from dagster._core.storage.partition_status_cache import get_partition_subsets


@whitelist_for_serdes
@record.record
class AssetMaterializationHealthState:
    """For tracking the materialization health of an asset, we only care about the most recent
    completed materialization attempt for each asset/partition. This record keeps track of the
    assets/partitions that are currently in a successful state and those that are in a failed state.
    If an asset/partition is currently being materialized, it will not move to a new state until after
    the materialization attempt is complete.

    In the future, we may want to expand this to track the last N materialization successes/failures for
    each asset. We could also maintain a list of in progress materializations, but that requires streamline to be
    better able to handle runs being deleted.
    """

    materialized_subset: SerializableEntitySubset[AssetKey]
    failed_subset: SerializableEntitySubset[AssetKey]
    partitions_snap: Optional[PartitionsSnap]

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        if self.partitions_snap is None:
            return None
        return self.partitions_snap.get_partitions_definition()

    @classmethod
    async def compute_for_asset(
        cls,
        asset_key: AssetKey,
        partitions_def: Optional[PartitionsDefinition],
        loading_context: LoadingContext,
    ) -> "AssetMaterializationHealthState":
        if partitions_def is not None:
            (
                materialized_partition_subset,
                failed_partition_subset,
                _,
            ) = get_partition_subsets(
                loading_context.instance,
                loading_context,
                asset_key,
                loading_context.instance,
                partitions_def,
            )

            if materialized_partition_subset is None or failed_partition_subset is None:
                check.failed("Expected partitions subset for a partitioned asset")

            return cls(
                materialized_subset=SerializableEntitySubset(
                    key=asset_key, value=materialized_partition_subset
                ),
                failed_subset=SerializableEntitySubset(
                    key=asset_key, value=failed_partition_subset
                ),
                partitions_snap=PartitionsSnap.from_def(partitions_def),
            )

        asset_record = await AssetRecord.gen(loading_context, asset_key)
        if asset_record is None:
            return AssetMaterializationHealthState(
                materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
                failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                partitions_snap=None,
            )

        asset_entry = asset_record.asset_entry
        if asset_entry.last_run_id is None:
            return AssetMaterializationHealthState(
                materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
                failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                partitions_snap=None,
            )

        has_ever_materialized = asset_entry.last_materialization is not None
        is_currently_failed = await _get_is_currently_failed(loading_context, asset_record)

        # it's possible that the asset is not materialized and not failed (ie if it has never been run)
        is_currently_materialized = has_ever_materialized and not is_currently_failed

        return cls(
            materialized_subset=SerializableEntitySubset(
                key=asset_key, value=is_currently_materialized
            ),
            failed_subset=SerializableEntitySubset(key=asset_key, value=is_currently_failed),
            partitions_snap=None,
        )


async def _get_is_currently_failed(
    loading_context: LoadingContext, asset_record: AssetRecord
) -> bool:
    asset_entry = asset_record.asset_entry
    if loading_context.instance.can_read_failure_events_for_asset(asset_record):
        latest_record = max(
            [
                asset_entry.last_materialization_record,
                asset_entry.last_failed_to_materialize_record,
            ],
            key=lambda record: -1 if record is None else record.storage_id,
        )
        return latest_record.storage_id == asset_entry.last_failed_to_materialize_storage_id

    # if failure events are not stored, we usually have to fetch the run record to check if the
    # asset is currently failed. However, if the latest run id is the same as the last materialization run id,
    # then we know the asset is in a successfully materialized state.
    if asset_entry.last_run_id == asset_entry.last_materialization.run_id:
        return False

    run_record = await RunRecord.gen(loading_context, asset_entry.last_run_id)
    if run_record is None or not run_record.dagster_run.is_finished:
        # the run is deleted or in progress. With the information we have available, we cannot know
        # if the asset is in a failed state prior to this run, so we report it as not failed
        return False

    run_end_time = check.not_none(run_record.end_time)
    if (
        asset_entry.last_materialization
        and asset_entry.last_materialization.timestamp > run_end_time
    ):
        # the latest materialization was reported manually
        return False

    # if the run failed, then report the asset as failed
    return run_record.dagster_run.is_failure
