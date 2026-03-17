from collections.abc import Mapping
from typing import Generic

from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_key import T_EntityKey
from dagster._record import record


@record
class TimingMetadata(Generic[T_EntityKey]):
    """Encapsulates per-timestamp entity subsets from an AutomationResult.

    Stores a mapping from event timestamp to the EntitySubset that occurred at that
    timestamp. Used by SinceCondition to make timestamp-precise decisions when both
    trigger and reset conditions fire on the same evaluation tick.
    """

    timestamps: Mapping[float, EntitySubset[T_EntityKey]]

    def subset_with_later_timestamps_than(
        self,
        other: "TimingMetadata[T_EntityKey]",
        empty: EntitySubset[T_EntityKey],
    ) -> EntitySubset[T_EntityKey]:
        """Returns the subset where self has a later timestamp than other."""
        result = empty
        for self_ts, self_subset in self.timestamps.items():
            to_add = self_subset
            for other_ts, other_subset in other.timestamps.items():
                if other_ts >= self_ts:
                    to_add = to_add.compute_difference(other_subset)
            result = result.compute_union(to_add)
        return result
