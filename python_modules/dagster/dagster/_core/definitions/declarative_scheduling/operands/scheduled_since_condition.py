import datetime
from typing import Sequence, cast

from dagster._core.definitions.declarative_scheduling.scheduling_evaluation_info import (
    AssetSliceWithMetadata,
)
from dagster._core.definitions.declarative_scheduling.utils import SerializableTimeDelta
from dagster._core.definitions.metadata.metadata_value import MetadataValue
from dagster._serdes.serdes import whitelist_for_serdes

from ..scheduling_condition import SchedulingCondition, SchedulingResult
from ..scheduling_context import SchedulingContext

_REQUEST_TIMESTAMP_METADATA_KEY = "request_timestamp"


@whitelist_for_serdes
class ScheduledSinceCondition(SchedulingCondition):
    """SchedulingCondition which is true if the asset has been requested for materialization via
    the declarative scheduling system within the given time window.

    Will only detect requests which have been made since this condition was added to the asset.
    """

    serializable_lookback_timedelta: SerializableTimeDelta

    @property
    def description(self) -> str:
        return f"Has been requested within the last {self.lookback_timedelta}"

    @property
    def lookback_timedelta(self) -> datetime.timedelta:
        return self.serializable_lookback_timedelta.to_timedelta()

    @staticmethod
    def from_lookback_delta(lookback_delta: datetime.timedelta) -> "ScheduledSinceCondition":
        return ScheduledSinceCondition(
            serializable_lookback_timedelta=SerializableTimeDelta.from_timedelta(lookback_delta)
        )

    def _get_minimum_timestamp(self, context: SchedulingContext) -> float:
        """The minimum timestamp for a request to be considered in the lookback window."""
        return (context.effective_dt - self.lookback_timedelta).timestamp()

    def _get_new_slices_with_metadata(
        self, context: SchedulingContext
    ) -> Sequence[AssetSliceWithMetadata]:
        """Updates the stored information as to when the asset was last requested."""
        # the first time this asset has been evaluated
        if context.previous_evaluation_info is None:
            return []

        previous_slices_with_metadata = (
            context.previous_evaluation_node.slices_with_metadata
            if context.previous_evaluation_node
            else []
        )

        # no new updates since previous tick
        if context.previous_requested_slice is None:
            return previous_slices_with_metadata

        # for existing subsets, remove references to newly-requested partitions, as these subsets
        # are meant to represent the most recent time that the asset was requested
        slices_with_metadata = [
            AssetSliceWithMetadata(
                asset_slice.compute_difference(context.previous_requested_slice), metadata
            )
            for asset_slice, metadata in previous_slices_with_metadata
        ]

        # for the newly-requested slice, add a new entry indicating that these partitions were
        # requested on the previous tick
        previous_request_timestamp = (
            context.previous_evaluation_info.temporal_context.effective_dt.timestamp()
        )
        slices_with_metadata.append(
            AssetSliceWithMetadata(
                context.previous_requested_slice,
                {_REQUEST_TIMESTAMP_METADATA_KEY: MetadataValue.float(previous_request_timestamp)},
            )
        )

        # finally, evict any empty subsets from the list, and any subsets with an older timestamp
        return [
            asset_slice_with_metadata
            for asset_slice_with_metadata in slices_with_metadata
            if not (
                asset_slice_with_metadata.asset_slice.is_empty
                or cast(
                    float,
                    asset_slice_with_metadata.metadata.get(
                        _REQUEST_TIMESTAMP_METADATA_KEY, MetadataValue.float(0)
                    ).value,
                )
                < self._get_minimum_timestamp(context)
            )
        ]

    def evaluate(self, context: SchedulingContext) -> SchedulingResult:
        slices_with_metadata = self._get_new_slices_with_metadata(context)

        # we keep track of all slices that have been requested within the lookback window, so we can
        # simply compute the union of all of these slices to determine the true slice
        requested_within_lookback_slice = context.asset_graph_view.create_empty_slice(
            context.asset_key
        )
        for asset_slice, _ in slices_with_metadata:
            requested_within_lookback_slice = requested_within_lookback_slice.compute_union(
                asset_slice
            )

        return SchedulingResult.create(
            context=context,
            true_slice=context.candidate_slice.compute_intersection(
                requested_within_lookback_slice
            ),
            slices_with_metadata=slices_with_metadata,
        )
