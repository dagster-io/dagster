import datetime
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple

import pendulum

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.asset_subset import AssetSubset
from dagster._core.definitions.declarative_scheduling.serialized_objects import (
    AssetConditionSnapshot,
    AssetSubsetWithMetadata,
)
from dagster._core.definitions.metadata import MetadataMapping
from dagster._model import DagsterModel
from dagster._serdes.serdes import PackableValue
from dagster._utils.security import non_secure_md5_hash_str

if TYPE_CHECKING:
    from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

    from .operands import (
        FailedSchedulingCondition,
        InLatestTimeWindowCondition,
        InProgressSchedulingCondition,
        MissingSchedulingCondition,
        ParentNewerCondition,
        RequestedThisTickCondition,
        ScheduledSinceCondition,
        UpdatedSinceCronCondition,
    )
    from .operators import (
        AllDepsCondition,
        AndAssetCondition,
        AnyDepsCondition,
        NotAssetCondition,
        OrAssetCondition,
    )
    from .scheduling_context import SchedulingContext


@experimental
class SchedulingCondition(ABC, DagsterModel):
    @property
    def children(self) -> Sequence["SchedulingCondition"]:
        return []

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()

    def get_snapshot(self, unique_id: str) -> AssetConditionSnapshot:
        """Returns a snapshot of this condition that can be used for serialization."""
        return AssetConditionSnapshot(
            class_name=self.__class__.__name__,
            description=self.description,
            unique_id=unique_id,
        )

    def get_unique_id(self, *, parent_unique_id: Optional[str], index: Optional[int]) -> str:
        """Returns a unique identifier for this condition within the broader condition tree."""
        parts = [str(parent_unique_id), str(index), self.__class__.__name__, self.description]
        return non_secure_md5_hash_str("".join(parts).encode())

    def as_auto_materialize_policy(self) -> "AutoMaterializePolicy":
        """Returns an AutoMaterializePolicy which contains this condition."""
        from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy

        return AutoMaterializePolicy.from_scheduling_condition(self)

    @abstractmethod
    def evaluate(self, context: "SchedulingContext") -> "SchedulingResult":
        raise NotImplementedError()

    def __and__(self, other: "SchedulingCondition") -> "AndAssetCondition":
        from .operators import AndAssetCondition

        # group AndAssetConditions together
        if isinstance(self, AndAssetCondition):
            return AndAssetCondition(operands=[*self.operands, other])
        return AndAssetCondition(operands=[self, other])

    def __or__(self, other: "SchedulingCondition") -> "OrAssetCondition":
        from .operators import OrAssetCondition

        # group OrAssetConditions together
        if isinstance(self, OrAssetCondition):
            return OrAssetCondition(operands=[*self.operands, other])
        return OrAssetCondition(operands=[self, other])

    def __invert__(self) -> "NotAssetCondition":
        from .operators import NotAssetCondition

        return NotAssetCondition(operand=self)

    @staticmethod
    def any_deps_match(condition: "SchedulingCondition") -> "AnyDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of any of its dependencies evaluate to True for the given condition.
        """
        from .operators import AnyDepsCondition

        return AnyDepsCondition(operand=condition)

    @staticmethod
    def all_deps_match(condition: "SchedulingCondition") -> "AllDepsCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one partition
        of all of its dependencies evaluate to True for the given condition.
        """
        from .operators import AllDepsCondition

        return AllDepsCondition(operand=condition)

    @staticmethod
    def missing() -> "MissingSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has never been
        materialized or observed.
        """
        from .operands import MissingSchedulingCondition

        return MissingSchedulingCondition()

    @staticmethod
    def in_progress() -> "InProgressSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it is part of an in-progress run."""
        from .operands import InProgressSchedulingCondition

        return InProgressSchedulingCondition()

    @staticmethod
    def failed() -> "FailedSchedulingCondition":
        """Returns a SchedulingCondition that is true for an asset partition if its latest run failed."""
        from .operands import FailedSchedulingCondition

        return FailedSchedulingCondition()

    @staticmethod
    def updated_since_cron(
        cron_schedule: str, cron_timezone: str = "UTC"
    ) -> "UpdatedSinceCronCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has been updated
        since the latest tick of the provided cron schedule.
        """
        from .operands import UpdatedSinceCronCondition

        return UpdatedSinceCronCondition(cron_schedule=cron_schedule, cron_timezone=cron_timezone)

    @staticmethod
    def in_latest_time_window(
        lookback_delta: Optional[datetime.timedelta] = None,
    ) -> "InLatestTimeWindowCondition":
        """Returns a SchedulingCondition that is true for an asset partition when it is within the latest
        time window.

        Args:
            lookback_delta (Optional, datetime.timedelta): If provided, the condition will
                return all partitions within the provided delta of the end of the latest time window.
                For example, if this is used on a daily-partitioned asset with a lookback_delta of
                48 hours, this will return the latest two partitions.
        """
        from .operands import InLatestTimeWindowCondition

        return InLatestTimeWindowCondition.from_lookback_delta(lookback_delta)

    @staticmethod
    def scheduled_since(lookback_delta: datetime.timedelta) -> "ScheduledSinceCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it has been requested
        for materialization via the declarative scheduling system within the given time window.

        Will only detect requests which have been made since this condition was added to the asset.

        Args:
            lookback_delta (datetime.timedelta): How far back in time to look for requests, e.g.
                if this is set to 1 hour, this rule will be true for a given asset partition for
                1 hour starting from the latest tick on which it gets requested.
        """
        from .operands import ScheduledSinceCondition

        return ScheduledSinceCondition.from_lookback_delta(lookback_delta)

    @staticmethod
    def requested_this_tick() -> "RequestedThisTickCondition":
        """Returns a SchedulingCondition that is true for an asset partition if it will be requested this tick."""
        from .operands import RequestedThisTickCondition

        return RequestedThisTickCondition()

    @staticmethod
    def parent_newer() -> "ParentNewerCondition":
        """Returns a SchedulingCondition that is true for an asset partition if at least one of its parents is newer."""
        from .operands import ParentNewerCondition

        return ParentNewerCondition()

    @staticmethod
    def eager_with_rate_limit(
        *,
        failure_retry_delta: datetime.timedelta = datetime.timedelta(hours=1),
    ) -> "SchedulingCondition":
        """Returns a condition which will "eagerly" fill in missing partitions as they are created,
        and ensures unpartitioned assets are updated whenever their dependencies are updated (either
        via scheduled execution or ad-hoc runs).

        Specifically, this is a composite SchedulingCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - At least one of its parents has been updated more recently than it, or the asset partition
            has never been materialized
        - None of its parent partitions are missing
        - None of its parent partitions are currently part of an in-progress run
        - It is not currently part of an in-progress run

        It will also refuse to materialize an asset partition if the latest materialization attempt
        failed and has not already been scheduled within the failure_retry_delta, to prevent
        repeated failures.
        """
        missing_or_parent_updated = (
            SchedulingCondition.parent_newer()
            | SchedulingCondition.any_deps_match(SchedulingCondition.requested_this_tick())
            | SchedulingCondition.missing()
        )
        any_parent_missing = SchedulingCondition.any_deps_match(
            SchedulingCondition.missing() & ~SchedulingCondition.requested_this_tick()
        )
        any_parent_in_progress = SchedulingCondition.any_deps_match(
            SchedulingCondition.in_progress()
        )
        failed_recently = SchedulingCondition.failed() & SchedulingCondition.scheduled_since(
            failure_retry_delta
        )
        return (
            SchedulingCondition.in_latest_time_window()
            & missing_or_parent_updated
            & ~any_parent_missing
            & ~any_parent_in_progress
            & ~SchedulingCondition.in_progress()
            & ~failed_recently
        )

    @staticmethod
    def on_cron(cron_schedule: str, cron_timezone: str = "UTC") -> "SchedulingCondition":
        """Returns a condition which will materialize asset partitions within the latest time window
        on a given cron schedule, after their parents have been updated. For example, if the
        cron_schedule is set to "0 0 * * *" (every day at midnight), then this rule will not become
        true on a given day until all of its parents have been updated during that same day.

        Specifically, this is a composite SchedulingCondition which is true for an asset partition
        if all of the following are true:

        - The asset partition is within the latest time window
        - All parent asset partitions have been updated since the latest tick of the provided cron
            schedule, or will be requested this tick
        - The asset partition has not been updated since the latest tick of the provided cron schedule
        - The asset partition is not currently part of an in-progress run
        """
        all_parents_updated_or_will_update = ~SchedulingCondition.any_deps_match(
            ~(
                SchedulingCondition.updated_since_cron(cron_schedule, cron_timezone)
                | SchedulingCondition.requested_this_tick()
            )
        )
        return (
            SchedulingCondition.in_latest_time_window()
            & all_parents_updated_or_will_update
            & ~SchedulingCondition.updated_since_cron(cron_schedule, cron_timezone)
            & ~SchedulingCondition.in_progress()
        )


class SchedulingResult(DagsterModel):
    condition: SchedulingCondition
    condition_unique_id: str
    start_timestamp: float
    end_timestamp: float

    true_slice: AssetSlice
    candidate_subset: AssetSubset
    subsets_with_metadata: Sequence[AssetSubsetWithMetadata]

    extra_state: Any
    child_results: Sequence["SchedulingResult"]

    @property
    def true_subset(self) -> AssetSubset:
        return self.true_slice.convert_to_valid_asset_subset()

    @staticmethod
    def create_from_children(
        context: "SchedulingContext",
        true_slice: AssetSlice,
        child_results: Sequence["SchedulingResult"],
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given child results."""
        return SchedulingResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.create_time.timestamp(),
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=true_slice,
            candidate_subset=context.candidate_slice.convert_to_valid_asset_subset(),
            subsets_with_metadata=[],
            child_results=child_results,
            extra_state=None,
        )

    @staticmethod
    def create(
        context: "SchedulingContext",
        true_slice: AssetSlice,
        subsets_with_metadata: Sequence[AssetSubsetWithMetadata] = [],
        slices_with_metadata: Sequence[Tuple[AssetSlice, MetadataMapping]] = [],
        extra_state: PackableValue = None,
    ) -> "SchedulingResult":
        """Returns a new AssetConditionEvaluation from the given parameters."""
        check.param_invariant(
            not (bool(subsets_with_metadata) and bool(slices_with_metadata)),
            "slices_with_metadata",
            "Cannot provide both subsets_with_metadata and slices_with_metadata.",
        )
        if slices_with_metadata:
            subsets_with_metadata = [
                AssetSubsetWithMetadata(
                    subset=asset_slice.convert_to_valid_asset_subset(), metadata=metadata
                )
                for asset_slice, metadata in slices_with_metadata
            ]
        return SchedulingResult(
            condition=context.condition,
            condition_unique_id=context.condition_unique_id,
            start_timestamp=context.create_time.timestamp(),
            end_timestamp=pendulum.now("UTC").timestamp(),
            true_slice=true_slice,
            candidate_subset=context.candidate_slice.convert_to_valid_asset_subset(),
            subsets_with_metadata=subsets_with_metadata,
            child_results=[],
            extra_state=extra_state,
        )
