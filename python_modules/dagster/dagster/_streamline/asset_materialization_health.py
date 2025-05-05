from typing import Optional

from dagster_graphql.implementation.fetch_assets import get_partition_subsets
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
    def default(cls, asset_key: AssetKey) -> "AssetMaterializationHealthState":
        return AssetMaterializationHealthState(
            materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
            failed_subset=SerializableEntitySubset(key=asset_key, value=False),
            partitions_snap=None,
        )

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
            return cls.default(asset_key)
        asset_entry = asset_record.asset_entry

        if loading_context.instance.can_read_failure_events_for_asset(asset_record):
            # compute the status based on the asset key table
            if (
                asset_entry.last_materialization_storage_id is None
                and asset_entry.last_failed_to_materialize_storage_id is None
            ):
                # never materialized
                return cls.default(asset_key)
            if asset_entry.last_failed_to_materialize_storage_id is None:
                # last_materialization_record must be non-null, therefore the asset successfully materialized
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=True),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                    partitions_snap=None,
                )
            elif asset_entry.last_materialization_storage_id is None:
                # last_failed_to_materialize_record must be non-null, therefore the asset failed to materialize
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=True),
                    partitions_snap=None,
                )

            if (
                asset_entry.last_materialization_storage_id
                > asset_entry.last_failed_to_materialize_storage_id
            ):
                # latest materialization succeeded
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=True),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                    partitions_snap=None,
                )
            # latest materialization failed
            return cls(
                materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
                failed_subset=SerializableEntitySubset(key=asset_key, value=True),
                partitions_snap=None,
            )
        # we are not storing failure events for this asset, so must compute status based on the information we have available
        # in some cases this results in reporting as asset as HEALTHY or UNKNOWN during an in progress run
        # even if the asset was previously failed
        else:
            # if the asset has been successfully materialized in the past, we fallback to that status
            # when we don't have the information available to compute status based on the latest run
            fallback_health_state = (
                cls.default(asset_key)
                if asset_entry.last_materialization is None
                else cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=True),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                    partitions_snap=None,
                )
            )
            if asset_entry.last_run_id is None:
                return fallback_health_state

            assert asset_entry.last_run_id is not None
            if (
                asset_entry.last_materialization is not None
                and asset_entry.last_run_id == asset_entry.last_materialization.run_id
            ):
                # latest materialization succeeded in the latest run
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=True),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                    partitions_snap=None,
                )
            run_record = await RunRecord.gen(loading_context, asset_entry.last_run_id)
            if run_record is None or not run_record.dagster_run.is_finished:
                return fallback_health_state
            run_end_time = check.not_none(run_record.end_time)
            if (
                asset_entry.last_materialization
                and asset_entry.last_materialization.timestamp > run_end_time
            ):
                # latest materialization was reported manually
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=True),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=False),
                    partitions_snap=None,
                )
            if run_record.dagster_run.is_failure:
                return cls(
                    materialized_subset=SerializableEntitySubset(key=asset_key, value=False),
                    failed_subset=SerializableEntitySubset(key=asset_key, value=True),
                    partitions_snap=None,
                )

            return fallback_health_state
