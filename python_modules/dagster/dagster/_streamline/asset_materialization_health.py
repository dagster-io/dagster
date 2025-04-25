from typing import Optional

from dagster_shared import record
from dagster_shared.serdes import whitelist_for_serdes

from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.remote_representation.external_data import PartitionsSnap
from dagster._streamline.asset_health import AssetHealthStatus


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

    materialized_subset: SerializableEntitySubset
    failed_subset: SerializableEntitySubset
    partitions_snap: Optional[PartitionsSnap]

    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        if self.partitions_snap is None:
            return None
        return self.partitions_snap.get_partitions_definition()

    @property
    def health_status(self) -> AssetHealthStatus:
        if self.failed_subset.size == 0 and self.materialized_subset.size == 0:
            return AssetHealthStatus.UNKNOWN
        if self.failed_subset.size > 0:
            return AssetHealthStatus.DEGRADED
        return AssetHealthStatus.HEALTHY
